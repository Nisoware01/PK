import os
import json
import re
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collections import defaultdict
from typing import Optional, List, Dict, Any
from .manual_match import log_rpc_benchmark_vector_poc
from .validator import validate_user_input
from .mm_mapper import full_part_number_pipeline

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "myuser"),
    "password": os.getenv("DB_PASSWORD", "mypassword")
}

app = FastAPI(title="Vector Match API", version="1.0")

class MatchRequest(BaseModel):
    part_number: str
    brand: Optional[str] = None
    top_k: int = 5
    min_similarity: float = 0.99

def find_similar_parts_local(embedding: List[float], top_k: int, min_similarity: float) -> List[Dict[str, Any]]:
    """
    Query the database to find parts similar to the given embedding.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        register_vector(conn)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM get_parts_by_specs_vector_poc(%s, %s, %s)
        """, (embedding, top_k, min_similarity))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        cursor.close()
        conn.close()

def match_part_number_with_regex(part_number: str, match_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Match the part number against regex patterns in the match results.
    """
    for match in match_results:
        try:
            pattern = match["regex"]
            if re.fullmatch(pattern, part_number):
                return match
        except re.error as e:
            print(f"❌ Invalid regex in DB: {pattern} → {e}")
            continue
    return None

def process_matches(input_match: Dict[str, Any], other_matches: List[Dict[str, Any]], validated_list: List[Any], request: MatchRequest) -> List[Dict[str, Any]]:
    """
    Process and filter the list of matches based on brand and similarity.
    """
    final_matches = []
    for match in other_matches:
        if input_match['brand'] != match['brand']:
            output_specs = match["specs"]
            output_map = match.get("specs_part_number_mapper", {})
            output_range_partnumber = match["part_number"]
            updated_input_specs, updated_output_specs, final_output_partnumber = full_part_number_pipeline(
                output_range_partnumber=output_range_partnumber,
                output_specs=output_specs,
                input_specs=input_match["specs"],
                input_map=input_match.get("specs_part_number_mapper", {}),
                output_map=output_map,
                data_list=validated_list
            )
            final_matches.append({
                "output_part_number": final_output_partnumber,
                "category": match['category'],
                "Brand": match["brand"],
                "updated_output_specs": updated_output_specs,
                "similarity": "Perfect Match" if input_match["notes"] == match["notes"] else "Partial Match",
                'notes': match['notes'],
                'environment_value': match['environment_value'],
                'similarity_vector': match['similarity'],
                'response_time_taken': match['duration_ms']
            })
            
    return final_matches

@app.post("/match-parts")
async def match_parts(request: MatchRequest):
    """
    Endpoint to match parts based on part number and optional brand.
    """
    match_results = log_rpc_benchmark_vector_poc(request.part_number)
    if not match_results:
        return {"error": f"{request.part_number} not found."}

    # Filter match results by brand if provided
    if request.brand:
        match_results = [m for m in match_results if m["brand"] == request.brand]
        if not match_results:
            return {"error": f"No matches found for brand '{request.brand}'."}
    else:
        # Check for ambiguity if brand not specified
        unique_brands_for_part = list({m["brand"] for m in match_results if m["part_number"] == request.part_number})
        if len(unique_brands_for_part) > 1:
            return {
                "error": f"Multiple brands found for part_number '{request.part_number}'.",
                "brands": unique_brands_for_part,
                "message": "Please specify the brand in your request."
            }
    matched_record = match_part_number_with_regex(request.part_number, match_results)
    if not matched_record:
        return {"error": f"No regex match found for part_number '{request.part_number}'"}

    regex = matched_record["regex"]
    ranges_json = matched_record["ranges_json"]
    valid_or_invalid, validated_list = validate_user_input(request.part_number, regex, ranges_json)
    if not valid_or_invalid:
        return {"error": f"{request.part_number} is invalid."}

    embedding = matched_record.get("specs_embedding")
    try:
        results = find_similar_parts_local(
            embedding=embedding,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        if not results:
            return {"error": f"{request.part_number} has no matches in the database."}

        input_match = None
        other_matches = []
        for item in results:
            if re.search(r'\[[^\]]+\]', item['part_number']) and not validated_list:
                continue
            value_iter = iter(validated_list)
            m_input_part_number = re.sub(
                r'\[[^\]]+\]',
                lambda m: str(int(v)) if isinstance((v := next(value_iter)), float) and v.is_integer() else str(v),
                item["part_number"]
            )
            if m_input_part_number == request.part_number:
                input_match = item
            else:
                other_matches.append(item)

        if not input_match:
            return {"error": f"Input part number '{request.part_number}' not found in results."}

        final_matches = process_matches(input_match, other_matches, validated_list, request)

        return {
            "input_part_number": request.part_number,
            "category": input_match['category'],
            "Brand": input_match['brand'],
            "input_part_number_data_specs": input_match["specs"],
            "notes": input_match['notes'],
            'environment_value': input_match['environment_value'],
            "matches": final_matches
        }

    except Exception as e:
        print(f"❌ Error in vector search: {e}")
        return {"error": f"Output matches not found at similarity {request.min_similarity}. Try again lowering it."}

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
from typing import Optional
from .manual_match import log_rpc_benchmark_vector_poc
from .validator import validate_user_input
from .mm_mapper import full_part_number_pipeline

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "myuser",
    "password": "mypassword"
}
app = FastAPI(title="Vector Match API", version="1.0")

class MatchRequest(BaseModel):
    part_number: str
    brand: Optional[str] = None
    top_k: int = 5
    min_similarity: float = 0.99


def find_similar_parts_local(embedding, top_k, min_similarity):
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

@app.post("/match-parts")
async def match_parts(request: MatchRequest):

    
    if request.part_number and request.brand:
        match_results = log_rpc_benchmark_vector_poc(request.part_number)
        single_partnumber = None
        if len(match_results) > 1:        
            for match in match_results:
                
                try:
                    pattern = match["regex"]
                    if re.fullmatch(pattern, request.part_number):  # or re.search if partial match is okay
                        single_partnumber = match
                        break  # Take the first fullmatch
                except re.error as e:
                    print(f"❌ Invalid regex in DB: {pattern} → {e}")
                    continue

            if not single_partnumber:
                return {
                    "error": f"No regex match found for part_number '{request.part_number}'"
                }

            match_results = [single_partnumber]  # Use best regex match only
            if len(match_results) == 1:
                record = match_results[0]
                regex = record["regex"]
                ranges_json = record["ranges_json"]
                valid_or_invalid, validated_list = validate_user_input(request.part_number, regex, ranges_json)
                
                if not valid_or_invalid:
                    return {"error": f"{request.part_number} is invalid."}

                embedding = record.get("specs_embedding")
                
                try:
                    results = find_similar_parts_local(
                        embedding=embedding,
                        top_k=2000,
                        min_similarity=request.min_similarity
                    )
                    if len(results) == 0:
                        return f"'{request.part_number} has no matches in the database."
                    input_match = None
                    other_matches = []

                    for item in results:
                        if re.search(r'\[[^\]]+\]', item['part_number']) and not validated_list: continue
                        value_iter = iter(validated_list)
                        m_input_part_number = re.sub(
                            r'\[[^\]]+\]',
                            lambda m: str(int(v)) if isinstance((v := next(value_iter)), float) and v.is_integer() else str(v),
                            item["part_number"]
        )
                        
                        if m_input_part_number == request.part_number and request.brand == item['brand']:
                            input_match = item
                        else:
                            other_matches.append(item)

                    # ✅ Run full pipeline for each similar output part
                    final_matches = []
                    print(len(other_matches))
                    for match in other_matches:
                        output_specs = match["specs"]
                        output_map = match.get("specs_part_number_mapper",{})
                        output_range_partnumber = match["part_number"]
                        
                        updated_input_specs, updated_output_specs, final_output_partnumber = full_part_number_pipeline(
                            output_range_partnumber=output_range_partnumber,
                            output_specs=output_specs,
                            input_specs=input_match["specs"],
                            input_map=input_match.get("specs_part_number_mapper", {}),
                            output_map=output_map,
                            data_list=validated_list  # 🔁 Replace with dynamic data_list if needed
                        )
                        print(final_output_partnumber)
                        if request.brand != match['brand'] :
                            final_matches.append({
                                "output_part_number": final_output_partnumber,
                                "category": match['category'],
                                "Brand":match["brand"],
                                "updated_output_specs": updated_output_specs,
                                "similarity":"Perfect Match" if match_results[0]["notes"] == match["notes"] else "Partial Match",
                                'notes':match['notes'],
                                'environment_value':match['environment_value'],
                                'similarity vecor':match['similarity'],
                                'response time taken': match['duration_ms']
                            })
                        if len(final_matches) > request.top_k - 1:
                            break    
                    print("first zone")
                    return {
                        "input_part_number": request.part_number,
                        "category": input_match['category'],
                        "Brand":request.brand,
                        "input_part_number_data_specs": updated_input_specs,
                        "notes":input_match['notes'],
                        'environment_value':input_match['environment_value'],
                        "matches": final_matches
                    }

                except Exception as e:
                    print(f"fourth ❌ Error in vector search: {e}")
                    return {"Minimum Similarity Error:": f'Output Matches not found at similarity {request.min_similarity}. Try again lowering it.'}

        else:
            return f"{request.part_number} not found."

    if not request.brand:
        
        match_results = log_rpc_benchmark_vector_poc(request.part_number)
        if len(match_results) == 0:
            return f"{request.part_number} not found."
        if len(match_results) > 1:
            same_brand = all(m["brand"] == match_results[0]["brand"] for m in match_results)
            if same_brand:
                single_partnumber = None
                
                for match in match_results:
                    
                    try:
                        pattern = match["regex"]
                        if re.fullmatch(pattern, request.part_number):  # or re.search if partial match is okay
                            single_partnumber = match
                            break  # Take the first fullmatch
                    except re.error as e:
                        print(f"❌ Invalid regex in DB: {pattern} → {e}")
                        continue

                if not single_partnumber:
                    return {
                        "error": f"No regex match found for part_number '{request.part_number}'"
                    }

                single_partnumber_list = [single_partnumber]  # Use best regex match only

                if len(single_partnumber_list) == 1:
                    record = single_partnumber_list[0]
                    regex = record["regex"]
                    ranges_json = record["ranges_json"]
                    valid_or_invalid, validated_list = validate_user_input(request.part_number, regex, ranges_json)
                    
                    if not valid_or_invalid:
                        return {"error": f"{request.part_number} is invalid."}

                    embedding = record.get("specs_embedding")
                    
                    try:
                        results = find_similar_parts_local(
                            embedding=embedding,
                            top_k=2000,
                            min_similarity=request.min_similarity
                        )
                        if len(results) == 0:
                            return f"'{request.part_number} has no matches in the database."
                        input_match = None
                        other_matches = []

                        for item in results:
                            if re.search(r'\[[^\]]+\]', item['part_number']) and not validated_list: continue
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

                        # ✅ Run full pipeline for each similar output part
                        final_matches = []
                        print(len(other_matches))
                        for match in other_matches:
                            output_specs = match["specs"]
                            print(match)
                            output_map = match.get("specs_part_number_mapper",{})
                            output_range_partnumber = match["part_number"]
                            
                            updated_input_specs, updated_output_specs, final_output_partnumber = full_part_number_pipeline(
                                output_range_partnumber=output_range_partnumber,
                                output_specs=output_specs,
                                input_specs=input_match["specs"],
                                input_map=input_match.get("specs_part_number_mapper", {}),
                                output_map=output_map,
                                data_list=validated_list  # 🔁 Replace with dynamic data_list if needed
                            )
                            
                            if input_match['brand'] != match['brand']:
                                final_matches.append({
                                    "output_part_number": final_output_partnumber,
                                    "category": match['category'],
                                    "Brand":match["brand"],
                                    "updated_output_specs": updated_output_specs,
                                    "similarity":"Perfect Match" if match_results[0]["notes"] == match["notes"] else "Partial Match",
                                    'notes':match['notes'],
                                    'environment_value':match['environment_value'],
                                    'similarity vecor':match['similarity'],
                                    'response time taken': match['duration_ms']
                                })
                            if len(final_matches) > request.top_k - 1:
                                break     
                        print("second zone")
                        return {
                            "input_part_number": request.part_number,
                            "category": input_match['category'],
                            "Brand":input_match['brand'],
                            "input_part_number_data_specs": updated_input_specs,
                            "notes":input_match['notes'],
                            'environment_value':input_match['environment_value'],
                            "matches": final_matches
                        }


                    except Exception as e:
                        print(f"first ❌ Error in vector search: {e}")
                        return {"Minimum Similarity Error:": f'Output Matches not found at similarity {request.min_similarity}. Try again lowering it.'}
            else:
                match_results_after_regex_check_for_different_brand = []
                for match in match_results:
                    try:
                        pattern = match["regex"]
                        print(pattern,request.part_number)
                        if re.fullmatch(pattern, request.part_number):  
                            match_results_after_regex_check_for_different_brand.append(match)

                    except re.error as e:
                        print(f"❌ Invalid regex in DB: {pattern} → {e}")
                        continue
                
                if len(match_results_after_regex_check_for_different_brand) == 0:
                    return {"error":f"No regex match found for '{request.part_number}'"}
                elif len(match_results_after_regex_check_for_different_brand) == 1:
                    record = match_results_after_regex_check_for_different_brand[0]
                    regex = record["regex"]
                    ranges_json = record["ranges_json"]
                    valid_or_invalid, validated_list = validate_user_input(request.part_number, regex, ranges_json)
                    
                    if not valid_or_invalid:
                        return {"error": f"{request.part_number} is invalid."}

                    embedding = record.get("specs_embedding")
                    
                    try:
                        results = find_similar_parts_local(
                            embedding=embedding,
                            top_k=2000,
                            min_similarity=request.min_similarity
                        )
                        if len(results) == 0:
                            return f"'{request.part_number} has no matches in the database."
                        input_match = None
                        other_matches = []

                        for item in results:
                            if re.search(r'\[[^\]]+\]', item['part_number']) and not validated_list: continue
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

                        # ✅ Run full pipeline for each similar output part
                        final_matches = []
                        
                        for match in other_matches:
                            output_specs = match["specs"]
                            output_map = match.get("specs_part_number_mapper",{})
                            output_range_partnumber = match["part_number"]
                            
                            updated_input_specs, updated_output_specs, final_output_partnumber = full_part_number_pipeline(
                                output_range_partnumber=output_range_partnumber,
                                output_specs=output_specs,
                                input_specs=input_match["specs"],
                                input_map=input_match.get("specs_part_number_mapper", {}),
                                output_map=output_map,
                                data_list=validated_list  # 🔁 Replace with dynamic data_list if needed
                            )
                            print(final_output_partnumber)
                            if input_match['brand'] != match['brand']:
                                final_matches.append({
                                    "output_part_number": final_output_partnumber,
                                    "category": match['category'],
                                    "Brand":match["brand"],
                                    "updated_output_specs": updated_output_specs,
                                    "similarity":"Perfect Match" if match_results[0]["notes"] == match["notes"] else "Partial Match",
                                    'notes':match['notes'],
                                    'environment_value':match['environment_value'],
                                    'similarity vecor':match['similarity'],
                                    'response time taken': match['duration_ms']
                                })

                            if len(final_matches) > request.top_k - 1:
                                break     
                        print("third zone")
                        return {
                            "input_part_number": request.part_number,
                            "category": input_match['category'],
                            "Brand":input_match['brand'],
                            "input_part_number_data_specs": updated_input_specs,
                            "notes":input_match['notes'],
                            'environment_value':input_match['environment_value'],
                            "matches": final_matches
                        }


                    except Exception as e:
                        print(f"second ❌ Error in vector search: {e}")
                        return {"Minimum Similarity Error:": f'Output Matches not found at similarity {request.min_similarity}. Try again lowering it.'}

                else:
                    simplified = [{"part_number": m["part_number"], "brand": m["brand"]} for m in match_results_after_regex_check_for_different_brand]
                    return {
                        "error": "Multiple matches found with different brands. Please specify the brand.",
                        "available_matches": simplified
                    }
        else:
            record = match_results[0]
            regex = record["regex"]
            ranges_json = record["ranges_json"]
            valid_or_invalid, validated_list = validate_user_input(request.part_number, regex, ranges_json)
            
            if not valid_or_invalid:
                return {"error": f"{request.part_number} is invalid."}

            embedding = record.get("specs_embedding")
            
            try:
                results = find_similar_parts_local(
                    embedding=embedding,
                    top_k=2000,
                    min_similarity=request.min_similarity
                )
                
                if len(results) == 0:
                    return f"'{request.part_number} has no matches in the database."
                input_match = None
                other_matches = []
                print(len(results))

                for item in results:
                    
                    # Skip iteration if validated_list is empty and part_number contains square brackets
                    if not validated_list and re.search(r'\[[^\]]+\]', item['part_number']):
                        print(f"Skipping item due to empty validated_list and brackets in part_number: {item['part_number']}")
                        continue

                    value_iter = iter(validated_list)
                    
                    m_input_part_number = re.sub(
                        r'\[[^\]]+\]',
                        lambda m: str(int(v)) if isinstance((v := next(value_iter)), float) and v.is_integer() else str(v),
                        item["part_number"]
                    )

                    
                    print(m_input_part_number, request.part_number)

                    if m_input_part_number == request.part_number:
                        input_match = item
                    else:
                        other_matches.append(item)

                print(input_match)
                # ✅ Run full pipeline for each similar output part
                final_matches = []
                print(len(other_matches))
                for match in other_matches:
                    output_specs = match["specs"]
                    
                    output_map = match.get("specs_part_number_mapper",{})
                    output_range_partnumber = match["part_number"]
                    
                    updated_input_specs, updated_output_specs, final_output_partnumber = full_part_number_pipeline(
                        output_range_partnumber=output_range_partnumber,
                        output_specs=output_specs,
                        input_specs=input_match["specs"],
                        input_map=input_match.get("specs_part_number_mapper", {}),
                        output_map=output_map,
                        data_list=validated_list  # 🔁 Replace with dynamic data_list if needed
                    )
                    print(final_output_partnumber)
                    print("fourth zone")
                    if input_match['brand'] != match['brand']:
                        final_matches.append({
                            "output_part_number": final_output_partnumber,
                            "category":match['category'],
                            "Brand":match["brand"],
                            "updated_output_specs": updated_output_specs,
                            "similarity":"Perfect Match" if match_results[0]["notes"] == match["notes"] else "Partial Match",
                            'notes':match['notes'],
                            'environment_value':match['environment_value'],
                            'similarity vecor':match['similarity'],
                            'response time taken': match['duration_ms']
                        })

                    if len(final_matches) > request.top_k - 1:
                        break     
                print(updated_input_specs)
                return {
                    "input_part_number": request.part_number,
                    "category":input_match['category'],
                    "Brand":input_match['brand'],
                    "input_part_number_data_specs": updated_input_specs,
                    "notes":input_match['notes'],
                    'environment_value':input_match['environment_value'],
                    "matches": final_matches
                }


            except Exception as e:
                print(f"third ❌ Error in vector search: {e}")
                # raise HTTPException(status_code=500, detail="Unexpected server error")
                return {"Minimum Similarity Error:": f'Output Matches not found at similarity {request.min_similarity}. Try again lowering it.'}


    
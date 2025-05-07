import os
import time
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from .static import get_static_part
# Load environment variables if needed
load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "myuser",
    "password": "mypassword"
}

def log_rpc_benchmark_vector(part_number: str, output_log_path="rpc_benchmark_log.jsonl"):
    start_time = time.time()

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # part_number = get_static_part(part_number)
        # print(part_number)
        # Call stored procedure or function
        cursor.execute("SELECT * FROM get_parts_by_first_static_part_vector(%s);", (part_number,))
        rows = cursor.fetchall()

        end_time = time.time()
        total_time = round((end_time - start_time) * 1000, 2)

        # Build result in dicts (assume columns are known, adjust as needed)
        colnames = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(colnames, row)) for row in rows]

        server_durations = [r.get("duration_ms") for r in result_dicts if r.get("duration_ms") is not None]

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "part_number": part_number,
            "total_time_ms": total_time,
            "response_size": len(rows),
            "avg_server_duration_ms": round(sum(server_durations) / len(server_durations), 2) if server_durations else None,
            "min_server_duration_ms": min(server_durations) if server_durations else None,
            "max_server_duration_ms": max(server_durations) if server_durations else None
        }

        # Save to log file
        with open(output_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        cursor.close()
        conn.close()

        return result_dicts

    except Exception as e:
        print("❌ Error during PostgreSQL RPC:", e)
        return []

def log_rpc_benchmark_vector_poc(part_number: str, output_log_path="rpc_benchmark_log.jsonl"):
    start_time = time.time()

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # part_number = get_static_part(part_number)
        # print(part_number)
        # Call stored procedure or function
        cursor.execute("SELECT * FROM get_parts_by_first_static_part_vector_poc(%s);", (part_number,))
        rows = cursor.fetchall()

        end_time = time.time()
        total_time = round((end_time - start_time) * 1000, 2)

        # Build result in dicts (assume columns are known, adjust as needed)
        colnames = [desc[0] for desc in cursor.description]
        result_dicts = [dict(zip(colnames, row)) for row in rows]

        server_durations = [r.get("duration_ms") for r in result_dicts if r.get("duration_ms") is not None]

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "part_number": part_number,
            "total_time_ms": total_time,
            "response_size": len(rows),
            "avg_server_duration_ms": round(sum(server_durations) / len(server_durations), 2) if server_durations else None,
            "min_server_duration_ms": min(server_durations) if server_durations else None,
            "max_server_duration_ms": max(server_durations) if server_durations else None
        }

        # Save to log file
        with open(output_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        cursor.close()
        conn.close()

        return result_dicts

    except Exception as e:
        print("❌ Error during PostgreSQL RPC:", e)
        return []


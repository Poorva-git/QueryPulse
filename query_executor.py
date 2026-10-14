"""
query_executor.py - Safely executes validated queries with timeout and clean JSON conversion
"""
import time
import json
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def execute_safe_query(engine: Engine, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    start_time = time.time()
    
    try:
        with engine.connect() as conn:
            # Set query timeout to prevent DB hangs (in milliseconds)
            conn.execute(text(f"SET statement_timeout = '{int(timeout_seconds * 1000)}';"))
            
            # Execute query and load into Pandas DataFrame
            df = pd.read_sql_query(text(query), conn)
            
        execution_time = round(time.time() - start_time, 3)

        # Fix: Convert numpy.int64, Decimal, and Timestamp safely to pure JSON
        records_json = df.to_json(orient="records", date_format="iso")
        safe_data = json.loads(records_json)

        return {
            "success": True,
            "data": safe_data,
            "columns": list(df.columns),
            "row_count": len(df),
            "execution_time_sec": execution_time,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time_sec": round(time.time() - start_time, 3),
            "error": str(e)
        }
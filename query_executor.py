"""
query_executor.py - Safe execution with statement timeout, JSON parsing, and EXPLAIN cost estimation
"""
import time
import json
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_query_plan_info(engine: Engine, query: str) -> Dict[str, Any]:
    """Runs EXPLAIN to calculate PostgreSQL query execution cost and primary scan type."""
    try:
        with engine.connect() as conn:
            res = conn.execute(text(f"EXPLAIN (FORMAT JSON) {query}"))
            plan_json = res.fetchone()[0]
            root = plan_json[0].get("Plan", {})
            return {
                "total_cost": round(root.get("Total Cost", 0.0), 2),
                "scan_type": root.get("Node Type", "Scan"),
                "success": True
            }
    except Exception:
        return {"total_cost": None, "scan_type": "Executed", "success": False}


def execute_safe_query(engine: Engine, query: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    start_time = time.time()
    plan_info = get_query_plan_info(engine, query)

    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET statement_timeout = '{int(timeout_seconds * 1000)}';"))
            df = pd.read_sql_query(text(query), conn)

        execution_time = round(time.time() - start_time, 3)

        records_json = df.to_json(orient="records", date_format="iso")
        safe_data = json.loads(records_json)

        return {
            "success": True,
            "data": safe_data,
            "columns": list(df.columns),
            "row_count": len(df),
            "execution_time_sec": execution_time,
            "plan_cost": plan_info.get("total_cost"),
            "scan_type": plan_info.get("scan_type"),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time_sec": round(time.time() - start_time, 3),
            "plan_cost": None,
            "scan_type": None,
            "error": str(e)
        }
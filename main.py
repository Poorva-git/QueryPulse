"""
main.py - FastAPI Backend with BYODB Custom Sessions, AST Security, and Dashboard
"""
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import (
    get_engine_for_db, get_available_databases, check_db_connection, DEFAULT_DB,
    create_custom_session_engine, get_session_engine, clear_session_engine
)
from schema_extractor import get_formatted_schema, extract_schema_metadata
from llm_sql import generate_sql_query
from sql_validator import validate_and_sanitize_sql
from query_executor import execute_safe_query
from insight_generator import generate_business_insight

app = FastAPI(title="QueryPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

QUERY_HISTORY: List[Dict[str, Any]] = []
SCHEMA_TEXT_CACHE: Dict[str, str] = {}
SCHEMA_METADATA_CACHE: Dict[str, Dict[str, Any]] = {}
CURRENT_DB = DEFAULT_DB


def get_schema_for_engine(cache_key: str, eng):
    if cache_key not in SCHEMA_TEXT_CACHE or cache_key not in SCHEMA_METADATA_CACHE:
        SCHEMA_TEXT_CACHE[cache_key] = get_formatted_schema(eng)
        SCHEMA_METADATA_CACHE[cache_key] = extract_schema_metadata(eng)
    return SCHEMA_TEXT_CACHE[cache_key], SCHEMA_METADATA_CACHE[cache_key]


@app.on_event("startup")
def startup_event():
    try:
        eng = get_engine_for_db(DEFAULT_DB)
        get_schema_for_engine(DEFAULT_DB, eng)
    except Exception as e:
        print(f"Startup cache warning: {e}")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))


class QuestionRequest(BaseModel):
    question: str
    database: Optional[str] = None
    session_id: Optional[str] = None


class SwitchDbRequest(BaseModel):
    database: str


class CustomDbRequest(BaseModel):
    session_id: str
    connection_uri: str


@app.get("/databases")
def list_databases():
    dbs = get_available_databases()
    return {"databases": dbs, "current_database": CURRENT_DB}


@app.post("/switch-db")
def switch_database(req: SwitchDbRequest):
    global CURRENT_DB
    db_name = req.database.strip()
    if not check_db_connection(db_name):
        raise HTTPException(status_code=400, detail=f"Cannot connect to database '{db_name}'.")
    CURRENT_DB = db_name
    eng = get_engine_for_db(db_name)
    _, metadata = get_schema_for_engine(db_name, eng)
    return {"status": "success", "active_database": CURRENT_DB, "tables": metadata}


@app.post("/connect-custom-db")
def connect_custom_db(req: CustomDbRequest):
    """Allows a user/recruiter to connect their own PostgreSQL database securely via session."""
    try:
        eng = create_custom_session_engine(req.session_id, req.connection_uri)
        cache_key = f"custom_{req.session_id}"
        _, metadata = get_schema_for_engine(cache_key, eng)
        return {
            "status": "success", 
            "message": "Custom PostgreSQL connected successfully!", 
            "tables": metadata,
            "table_count": len(metadata)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Connection Failed: {str(e)}")


@app.post("/disconnect-custom-db")
def disconnect_custom_db(session_id: str):
    clear_session_engine(session_id)
    cache_key = f"custom_{session_id}"
    SCHEMA_TEXT_CACHE.pop(cache_key, None)
    SCHEMA_METADATA_CACHE.pop(cache_key, None)
    return {"status": "success", "message": "Reverted to Demo Sandbox"}


@app.get("/tables")
def get_tables(db: Optional[str] = None, session_id: Optional[str] = None):
    if session_id and f"custom_{session_id}" in SCHEMA_METADATA_CACHE:
        return SCHEMA_METADATA_CACHE[f"custom_{session_id}"]

    target_db = db or CURRENT_DB
    eng = get_engine_for_db(target_db)
    _, metadata = get_schema_for_engine(target_db, eng)
    return metadata


@app.get("/history")
def get_history():
    return QUERY_HISTORY[-20:]


@app.post("/ask")
def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Determine target engine & schema
    if request.session_id and f"custom_{request.session_id}" in SCHEMA_TEXT_CACHE:
        cache_key = f"custom_{request.session_id}"
        schema_text = SCHEMA_TEXT_CACHE[cache_key]
        eng = get_session_engine(request.session_id, CURRENT_DB)
        db_label = "Custom DB"
    else:
        target_db = request.database or CURRENT_DB
        eng = get_engine_for_db(target_db)
        schema_text, _ = get_schema_for_engine(target_db, eng)
        db_label = target_db

    # 1. NL to SQL
    try:
        raw_sql = generate_sql_query(question, schema_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

    # 2. AST Security Validation
    is_valid, val_error, sanitized_sql = validate_and_sanitize_sql(raw_sql)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Security Blocked: {val_error}")

    # 3. Execution + EXPLAIN Plan
    exec_result = execute_safe_query(eng, sanitized_sql)
    if not exec_result["success"]:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {exec_result['error']}")

    # 4. AI Insight
    insight = generate_business_insight(question, sanitized_sql, exec_result["data"])

    # 5. Save History
    history_entry = {
        "database": db_label,
        "question": question,
        "sql": sanitized_sql,
        "rows": exec_result["row_count"],
        "time_sec": exec_result["execution_time_sec"],
        "scan_type": exec_result["scan_type"]
    }
    QUERY_HISTORY.append(history_entry)

    return {
        "database": db_label,
        "question": question,
        "sql": sanitized_sql,
        "data": exec_result["data"],
        "columns": exec_result["columns"],
        "row_count": exec_result["row_count"],
        "execution_time_sec": exec_result["execution_time_sec"],
        "plan_cost": exec_result["plan_cost"],
        "scan_type": exec_result["scan_type"],
        "insight": insight
    }
"""
main.py - FastAPI Backend with Multi-Database Switching and Static Dashboard
"""
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import get_engine_for_db, get_available_databases, check_db_connection, DEFAULT_DB
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

# In-memory caches per database
SCHEMA_TEXT_CACHE: Dict[str, str] = {}
SCHEMA_METADATA_CACHE: Dict[str, Dict[str, Any]] = {}

CURRENT_DB = DEFAULT_DB


def get_db_schema(db_name: str):
    """Retrieves or builds schema cache for a specific database."""
    if db_name not in SCHEMA_TEXT_CACHE or db_name not in SCHEMA_METADATA_CACHE:
        eng = get_engine_for_db(db_name)
        SCHEMA_TEXT_CACHE[db_name] = get_formatted_schema(eng)
        SCHEMA_METADATA_CACHE[db_name] = extract_schema_metadata(eng)
        print(f"Schema cached for database: {db_name}")
    return SCHEMA_TEXT_CACHE[db_name], SCHEMA_METADATA_CACHE[db_name]


@app.on_event("startup")
def startup_event():
    try:
        get_db_schema(DEFAULT_DB)
    except Exception as e:
        print(f"Initial schema caching error: {e}")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))


class QuestionRequest(BaseModel):
    question: str
    database: Optional[str] = None


class SwitchDbRequest(BaseModel):
    database: str


@app.get("/databases")
def list_databases():
    """Lists available databases and current selected database."""
    dbs = get_available_databases()
    return {"databases": dbs, "current_database": CURRENT_DB}


@app.post("/switch-db")
def switch_database(req: SwitchDbRequest):
    """Switches active database and returns its tables."""
    global CURRENT_DB
    db_name = req.database.strip()
    if not check_db_connection(db_name):
        raise HTTPException(status_code=400, detail=f"Cannot connect to database '{db_name}'. Check credentials.")
    CURRENT_DB = db_name
    _, metadata = get_db_schema(db_name)
    return {"status": "success", "active_database": CURRENT_DB, "tables": metadata}


@app.get("/tables")
def get_tables(db: Optional[str] = None):
    target_db = db or CURRENT_DB
    _, metadata = get_db_schema(target_db)
    return metadata


@app.get("/history")
def get_history():
    return QUERY_HISTORY[-20:]


@app.post("/ask")
def ask_question(request: QuestionRequest):
    target_db = request.database or CURRENT_DB
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    schema_text, _ = get_db_schema(target_db)
    eng = get_engine_for_db(target_db)

    # 1. NL to SQL
    try:
        raw_sql = generate_sql_query(question, schema_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

    # 2. AST Security Validation
    is_valid, val_error, sanitized_sql = validate_and_sanitize_sql(raw_sql)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Security Blocked: {val_error}")

    # 3. Execution
    exec_result = execute_safe_query(eng, sanitized_sql)
    if not exec_result["success"]:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {exec_result['error']}")

    # 4. Insight
    insight = generate_business_insight(question, sanitized_sql, exec_result["data"])

    # 5. History
    history_entry = {
        "database": target_db,
        "question": question,
        "sql": sanitized_sql,
        "rows": exec_result["row_count"],
        "time_sec": exec_result["execution_time_sec"]
    }
    QUERY_HISTORY.append(history_entry)

    return {
        "database": target_db,
        "question": question,
        "sql": sanitized_sql,
        "data": exec_result["data"],
        "columns": exec_result["columns"],
        "row_count": exec_result["row_count"],
        "execution_time_sec": exec_result["execution_time_sec"],
        "insight": insight
    }
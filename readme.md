# ⚡ QueryPulse — Complete System Architecture & Master Guide

> **Live Interactive Demo:** [https://querypulse-sok8.onrender.com/](https://querypulse-sok8.onrender.com/)  
> **GitHub Repository:** [https://github.com/Poorva-git/QueryPulse](https://github.com/Poorva-git/QueryPulse)  
> **Author:** Poorva Soni (Final Year B.Tech CSE Placement Portfolio Project)

---

## 📌 1. Project Overview & Pitch
**QueryPulse** is a zero-trust conversational data engine for PostgreSQL. It allows non-technical stakeholders to ask questions in plain English or Hinglish (e.g. *"Top 5 most rented films kaunsi hain?"*), translates intent into mathematically verified SQL, inspects internal PostgreSQL execution costs (`EXPLAIN`), executes queries safely with timeout safeguards, and renders interactive Chart.js visualizations alongside executive AI insights.

---

## 🏗️ 2. End-to-End System Architecture

```
[ User Prompt: English / Hinglish ]
                │
                ▼
   [ FastAPI Backend Endpoint: /ask ]
                │
                ├─► 1. Schema Extractor: Reads tables, columns & foreign keys from pg_catalog
                │
                ├─► 2. Groq LPU (GPT-o-120B): Generates deterministic, schema-aware SQL
                │
                ├─► 3. SQLGlot AST Sandbox: Verifies syntax tree (Blocks DDL/DML/DoS/Injections)
                │
                ├─► 4. Query Executor: Computes EXPLAIN plan cost + 5s statement_timeout
                │
                ├─► 5. Insight Generator: Produces 2-sentence executive business takeaways
                │
                ▼
   [ Single Page Dashboard: Chart.js + Tailwind CSS ]
   (Interactive Charts · Data Tables · SQL Display with Cost Badge · CSV Export)
```

---

## 🛡️ 3. Security Architecture (AST Guard vs RegEx)

Most text-to-SQL projects use regular expressions (`re.search(r"drop", sql)`), which are easily bypassed using SQL comments (e.g. `/*drop*/`) or hex encoding. QueryPulse uses **SQLGlot Abstract Syntax Tree (AST)** parsing:
1. **Multi-Statement Blocking:** Rejects queries containing semicolons or multiple AST roots.
2. **Read-Only DML Lock:** Only permits `exp.Select` statements. Rejects `INSERT`, `UPDATE`, `DELETE`.
3. **DDL Lockout:** Rejects `exp.Drop`, `exp.Alter`, `exp.Create`, `exp.Truncate`.
4. **DoS Shield:** Rejects blocking functions like `pg_sleep()` to prevent connection starvation.
5. **Filesystem Isolation:** Rejects server inspection functions like `pg_read_file()`.
6. **Row Clamping:** Enforces `LIMIT 1000` to prevent memory exhaustion.
7. **Timeout Safeguard:** Sets `SET statement_timeout = 5000` (5-second hard limit) before execution.

---

## 🔌 4. Bring Your Own Database (BYODB)
QueryPulse supports connecting any external PostgreSQL instance (Neon, Supabase, AWS RDS, local):
* Connections are tied to an ephemeral `session_id` stored in browser `sessionStorage`.
* Engines are isolated in server RAM and disposed upon session disconnect.
* Credentials are never persisted to disk or logs.

---

## 💻 5. Complete Consolidated Source Code

Below is the complete, unbroken source code of all core backend modules, security tests, and configuration:

### Module 1: `main.py` (FastAPI REST API & Endpoints)
```python
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

    raw_sql = generate_sql_query(question, schema_text)
    is_valid, val_error, sanitized_sql = validate_and_sanitize_sql(raw_sql)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Security Blocked: {val_error}")

    exec_result = execute_safe_query(eng, sanitized_sql)
    if not exec_result["success"]:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {exec_result['error']}")

    insight = generate_business_insight(question, sanitized_sql, exec_result["data"])

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
```

### Module 2: `sql_validator.py` (AST Security Sandbox)
```python
import sqlglot
from sqlglot import exp

FORBIDDEN_OPERATIONS = (
    exp.Drop, exp.Delete, exp.Update, exp.Insert, exp.Alter,
    exp.Create, exp.Truncate, exp.Merge
)
FORBIDDEN_FUNCTIONS = {"pg_sleep", "pg_read_file", "pg_write_file", "pg_read_binary_file", "version"}
MAX_ROW_LIMIT = 1000

def validate_and_sanitize_sql(sql_query: str):
    try:
        cleaned_sql = sql_query.strip().rstrip(";")
        statements = sqlglot.parse(cleaned_sql, read="postgres")
        if not statements or len(statements) == 0:
            return False, "Empty query received.", ""
        if len(statements) > 1:
            return False, "Security Violation: Multiple queries separated by semicolons are forbidden.", ""

        root = statements[0]
        if not isinstance(root, exp.Select):
            return False, f"Security Violation: Only SELECT queries are permitted. Blocked: {type(root).__name__}", ""

        for node in root.walk():
            if isinstance(node, FORBIDDEN_OPERATIONS):
                return False, f"Security Violation: Prohibited operation detected ({type(node).__name__}).", ""
            if isinstance(node, exp.Anonymous):
                if node.name.lower() in FORBIDDEN_FUNCTIONS:
                    return False, f"Security Violation: Prohibited function call '{node.name}'.", ""

        limit_node = root.args.get("limit")
        if limit_node is None:
            root = root.limit(MAX_ROW_LIMIT)
        else:
            try:
                current_limit = int(limit_node.expression.this)
                if current_limit > MAX_ROW_LIMIT:
                    root.args["limit"] = exp.Limit(this=exp.Literal.number(MAX_ROW_LIMIT))
            except Exception:
                root.args["limit"] = exp.Limit(this=exp.Literal.number(MAX_ROW_LIMIT))

        return True, None, root.sql(dialect="postgres")
    except Exception as e:
        return False, f"AST Syntax Error: Unable to validate SQL. {str(e)}", ""
```

### Module 3: `query_executor.py` (Execution & EXPLAIN Cost Analysis)
```python
import time
import json
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

def get_query_plan_info(engine: Engine, query: str) -> Dict[str, Any]:
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
```

### Module 4: `db.py` (Multi-Database & BYODB Session Engine)
```python
import os
import re
from typing import Dict, List
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file!")

match = re.match(r"(postgresql(?:\+[a-z0-9]+)?://[^/]+/)(.*)", DATABASE_URL)
if match:
    BASE_DB_URL = match.group(1)
    DEFAULT_DB = match.group(2) or "dvdrental"
else:
    BASE_DB_URL = DATABASE_URL.rsplit("/", 1)[0] + "/"
    DEFAULT_DB = "dvdrental"

ENGINES: Dict[str, Engine] = {}
SESSION_CUSTOM_ENGINES: Dict[str, Engine] = {}

def get_engine_for_db(db_name: str) -> Engine:
    db_name = db_name.strip()
    if db_name not in ENGINES:
        db_url = f"{BASE_DB_URL}{db_name}"
        ENGINES[db_name] = create_engine(db_url, pool_pre_ping=True)
    return ENGINES[db_name]

engine = get_engine_for_db(DEFAULT_DB)

def create_custom_session_engine(session_id: str, connection_uri: str) -> Engine:
    uri = connection_uri.strip()
    if uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)

    eng = create_engine(uri, pool_pre_ping=True, pool_size=3, max_overflow=2)
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))

    SESSION_CUSTOM_ENGINES[session_id] = eng
    return eng

def get_session_engine(session_id: str, db_name: str) -> Engine:
    if session_id in SESSION_CUSTOM_ENGINES:
        return SESSION_CUSTOM_ENGINES[session_id]
    return get_engine_for_db(db_name)

def clear_session_engine(session_id: str):
    if session_id in SESSION_CUSTOM_ENGINES:
        try:
            SESSION_CUSTOM_ENGINES[session_id].dispose()
        except Exception:
            pass
        del SESSION_CUSTOM_ENGINES[session_id]

def check_db_connection(db_name: str = DEFAULT_DB) -> bool:
    try:
        eng = get_engine_for_db(db_name)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def get_available_databases() -> List[str]:
    try:
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT datname FROM pg_database 
                WHERE datistemplate = false 
                AND datname NOT IN ('postgres')
                ORDER BY datname;
            """))
            dbs = [row[0] for row in res.fetchall()]
            return dbs if dbs else [DEFAULT_DB]
    except Exception:
        return ["dvdrental", "onlinebookstore"]
```

### Module 5: `schema_extractor.py` (Relational Catalog Extractor)
```python
from typing import Dict, Any
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

def extract_schema_metadata(engine: Engine) -> Dict[str, Any]:
    inspector = inspect(engine)
    metadata = {}
    for table_name in inspector.get_table_names(schema="public"):
        columns = []
        for col in inspector.get_columns(table_name, schema="public"):
            columns.append({"name": col["name"], "type": str(col["type"])})

        pk_constraint = inspector.get_pk_constraint(table_name, schema="public")
        pk_columns = pk_constraint.get("constrained_columns", [])

        fks = []
        for fk in inspector.get_foreign_keys(table_name, schema="public"):
            fks.append({
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"]
            })

        metadata[table_name] = {
            "columns": columns,
            "primary_keys": pk_columns,
            "foreign_keys": fks
        }
    return metadata

def get_formatted_schema(engine: Engine) -> str:
    metadata = extract_schema_metadata(engine)
    lines = []
    for table, details in metadata.items():
        lines.append(f"Table: {table}")
        lines.append("  Columns:")
        for col in details["columns"]:
            pk_flag = " [PK]" if col["name"] in details["primary_keys"] else ""
            lines.append(f"    - {col['name']} ({col['type']}){pk_flag}")
        if details["foreign_keys"]:
            lines.append("  Foreign Keys:")
            for fk in details["foreign_keys"]:
                lines.append(f"    - {fk['constrained_columns']} references {fk['referred_table']}({fk['referred_columns']})")
        lines.append("")
    return "\n".join(lines)
```

### Module 6: `llm_sql.py` (Groq LPU Text-to-SQL Generator)
```python
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generate_sql_query(user_question: str, schema_context: str) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    prompt = f"""You are an elite PostgreSQL DBA and data analyst.
Given the database schema below, generate a syntactically correct PostgreSQL SELECT query that answers the user's question.

CRITICAL RULES:
1. ONLY return the raw SQL query. Do NOT include markdown formatting, backticks, or conversational text.
2. The query MUST be a read-only SELECT query.
3. Understand natural language inquiries in both English and Hinglish (e.g. "kaunsi films", "sabse zyada", "top customer").
4. Use standard ANSI SQL / PostgreSQL syntax with explicit JOINs based on foreign keys.
5. Limit results to 1000 rows maximum.

DATABASE SCHEMA:
{schema_context}

USER QUESTION:
{user_question}
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    sql = response.choices[0].message.content.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()
```

### Module 7: `insight_generator.py` (AI Business Summarizer)
```python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generate_business_insight(question: str, sql: str, data: list) -> str:
    if not client or not data:
        return "Query executed successfully. View raw tabular data and visualizations below."
    try:
        sample_data = str(data[:5])
        prompt = f"""You are a Chief Data Officer presenting insights to executive stakeholders.
User Question: {question}
Executed SQL: {sql}
Result Sample: {sample_data}

Write exactly 2 concise, impactful sentences summarizing the key business takeaway from this data.
Focus on business value, metrics, and trends. Do NOT mention SQL syntax or table column names."""

        res = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=120
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return "Query executed successfully. View raw tabular data and visualizations below."
```

### Module 8: `tests/test_security.py` (Pytest Adversarial Test Suite)
```python
import pytest
from sql_validator import validate_and_sanitize_sql

def test_legitimate_select_query():
    sql = "SELECT title, release_year FROM film WHERE rating = 'PG-13'"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is True
    assert "LIMIT 1000" in sanitized

def test_row_limit_clamping():
    sql = "SELECT * FROM payment LIMIT 5000"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is True
    assert "LIMIT 1000" in sanitized

def test_block_multistatement_injection():
    sql = "SELECT * FROM customer; DROP TABLE customer CASCADE;"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False
    assert "multiple" in error.lower() or "forbidden" in error.lower()

def test_block_delete_dml():
    sql = "DELETE FROM rental WHERE rental_id = 1"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False

def test_block_drop_ddl():
    sql = "DROP TABLE film"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False

def test_block_update_dml():
    sql = "UPDATE staff SET active = false"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False

def test_block_pg_sleep_dos():
    sql = "SELECT title, pg_sleep(10) FROM film"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False
    assert "pg_sleep" in error

def test_block_file_read():
    sql = "SELECT pg_read_file('/etc/passwd')"
    is_valid, error, sanitized = validate_and_sanitize_sql(sql)
    assert is_valid is False
```

---

## 🎯 6. Technical Interview Questions & Answers

**Q1: Why did you choose AST validation over regular expressions?**  
*Answer:* RegEx operates on raw text and can easily be bypassed using comments like `/*drop*/` or nested clauses. SQLGlot parses SQL into an Abstract Syntax Tree where each semantic operation is a mathematical node. We inspect node types (`exp.Drop`, `exp.Delete`), completely neutralizing obfuscation.

**Q2: What is the purpose of EXPLAIN cost analysis in your pipeline?**  
*Answer:* In production, an AI query might accidentally cause unindexed Cartesian joins across millions of rows. By running `EXPLAIN (FORMAT JSON)` beforehand, QueryPulse extracts the PostgreSQL planner's cost units and scan type (e.g., `Index Scan` vs `Seq Scan`), providing immediate visibility into execution overhead.

**Q3: How does QueryPulse handle session isolation in the BYODB feature?**  
*Answer:* When a user enters their database credentials, an ephemeral `session_id` is assigned from the browser. The SQLAlchemy engine is registered in server memory under that key with connection pool limits (`pool_size=3, max_overflow=2`). Disconnecting disposes of the pool immediately, and zero credentials ever touch disk.

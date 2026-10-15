"""
db.py - Multi-Database Connection Engine with Custom URI Isolation
"""
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
    """Connects to a user's custom PostgreSQL database and verifies credentials."""
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
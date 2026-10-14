"""
db.py - Multi-Database Connection Engine for PostgreSQL
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

# Extract Base URL without database name (e.g., postgresql+psycopg2://postgres:pass@localhost:5432/)
match = re.match(r"(postgresql(?:\+[a-z0-9]+)?://[^/]+/)(.*)", DATABASE_URL)
if match:
    BASE_DB_URL = match.group(1)
    DEFAULT_DB = match.group(2) or "dvdrental"
else:
    BASE_DB_URL = DATABASE_URL.rsplit("/", 1)[0] + "/"
    DEFAULT_DB = "dvdrental"

# Engine cache dictionary
ENGINES: Dict[str, Engine] = {}


def get_engine_for_db(db_name: str) -> Engine:
    """Returns an active SQLAlchemy engine for the specified database name."""
    db_name = db_name.strip()
    if db_name not in ENGINES:
        db_url = f"{BASE_DB_URL}{db_name}"
        ENGINES[db_name] = create_engine(db_url, pool_pre_ping=True)
    return ENGINES[db_name]


# Initialize default engine
engine = get_engine_for_db(DEFAULT_DB)


def check_db_connection(db_name: str = DEFAULT_DB) -> bool:
    """Verifies connection to a specific database."""
    try:
        eng = get_engine_for_db(db_name)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Connection check error for {db_name}: {e}")
        return False


def get_available_databases() -> List[str]:
    """Fetches non-system databases from PostgreSQL."""
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
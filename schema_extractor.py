"""
schema_extractor.py
-------------------
Extracts PostgreSQL schema metadata using SQLAlchemy's Inspector.
"""

from typing import Dict, Any, List
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def extract_schema_metadata(engine: Engine) -> Dict[str, Any]:
    inspector = inspect(engine)
    schema_info: Dict[str, Any] = {}

    for table_name in inspector.get_table_names():
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = set(pk_constraint.get("constrained_columns", []))

        columns: List[Dict[str, Any]] = []
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "primary_key": col["name"] in primary_keys,
            })

        foreign_keys: List[Dict[str, Any]] = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"],
            })

        schema_info[table_name] = {
            "columns": columns,
            "foreign_keys": foreign_keys,
        }

    return schema_info


def format_schema_for_llm(schema_info: Dict[str, Any]) -> str:
    lines = []
    for table_name, details in schema_info.items():
        lines.append(f"Table: {table_name}")
        lines.append("  Columns:")
        for col in details["columns"]:
            pk_tag = " [PK]" if col["primary_key"] else ""
            lines.append(f"    - {col['name']} ({col['type']}){pk_tag}")

        if details["foreign_keys"]:
            lines.append("  Foreign Keys:")
            for fk in details["foreign_keys"]:
                from_cols = ", ".join(fk["constrained_columns"])
                to_cols = ", ".join(fk["referred_columns"])
                lines.append(f"    - ({from_cols}) -> {fk['referred_table']}({to_cols})")

        lines.append("")

    return "\n".join(lines).strip()


def get_formatted_schema(engine: Engine) -> str:
    metadata = extract_schema_metadata(engine)
    return format_schema_for_llm(metadata)
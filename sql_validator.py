"""
sql_validator.py - Security validation using AST parsing (sqlglot)
"""
from typing import Tuple, Optional
import sqlglot
from sqlglot import exp

FORBIDDEN_AST_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,          # <--- 'AlterTable' ki jagah 'Alter'
    exp.Create,
    exp.Command,
    exp.TruncateTable,
)

FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
}


def validate_and_sanitize_sql(
    sql_query: str, 
    max_limit: int = 1000
) -> Tuple[bool, Optional[str], Optional[str]]:
    if not sql_query or not sql_query.strip():
        return False, "Query khali hai.", None

    clean_sql = sql_query.strip().rstrip(";")

    try:
        statements = sqlglot.parse(clean_sql, read="postgres")
    except Exception as e:
        return False, f"SQL Syntax Error: {str(e)}", None

    if len(statements) != 1:
        return False, "Security Error: Sirf single query allowed hai, multiple queries blocked.", None

    stmt = statements[0]

    if not isinstance(stmt, exp.Select):
        return False, "Security Error: Sirf SELECT queries allowed hain.", None

    for node in stmt.walk():
        if isinstance(node, FORBIDDEN_AST_NODES):
            return False, f"Security Error: Forbidden operation ({type(node).__name__}) detected.", None

        if isinstance(node, exp.Anonymous) and node.name.lower() in FORBIDDEN_FUNCTIONS:
            return False, f"Security Error: Function '{node.name}' blocked.", None

    # Enforce row limit (max 1000)
    limit_node = stmt.find(exp.Limit)
    if limit_node:
        try:
            current_limit = int(limit_node.expression.this)
            if current_limit > max_limit:
                limit_node.set("expression", exp.Literal.number(max_limit))
        except Exception:
            limit_node.set("expression", exp.Literal.number(max_limit))
    else:
        stmt = stmt.limit(max_limit)

    return True, None, stmt.sql(dialect="postgres")
"""
tests/test_security.py - Adversarial security validation test suite
Run: pytest tests/test_security.py
"""
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
    assert "single query" in error.lower() or "multiple" in error.lower()


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
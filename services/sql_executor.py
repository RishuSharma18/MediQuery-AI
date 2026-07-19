"""
services/sql_executor.py
Validates then executes SQL against a read-only SQLite connection. This is
the safety gate: LLM-generated SQL passes through validate_sql() before it
ever touches the database.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from database.db import get_readonly_engine
from utils.logger import get_logger
from utils.validators import validate_sql, enforce_row_limit

logger = get_logger(__name__)


class SQLExecutionError(RuntimeError):
    pass


def execute_sql(sql: str, question: str = "") -> pd.DataFrame:
    """Validate then execute a single read-only SELECT. Raises SQLExecutionError
    on any validation failure or execution error."""
    validation = validate_sql(sql)

    if not validation.is_valid:
        logger.warning("Rejected unsafe SQL: %s | reason=%s", sql, validation.reason)
        raise SQLExecutionError(f"Query rejected for safety reasons: {validation.reason}")

    final_sql = enforce_row_limit(validation.cleaned_sql)

    try:
        ro_engine = get_readonly_engine()
        with ro_engine.connect() as conn:
            df = pd.read_sql(text(final_sql), conn)
        logger.info("Executed SQL for question '%s': %s rows returned", question, len(df))
        return df
    except Exception as e:
        logger.error("SQL execution failed: %s | error=%s", final_sql, e)
        raise SQLExecutionError(f"Query execution failed: {e}") from e
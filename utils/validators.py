"""
utils/validators.py
Safety validation for LLM-generated SQL before it is ever executed.

Design goals:
- Only a single read-only SELECT statement is allowed.
- Any statement-chaining, comments, or write/DDL keywords are rejected outright.
- This is defense-in-depth: the DB connection itself is also opened read-only
  (see database/db.py), so even a bypass here cannot mutate data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config import settings


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    cleaned_sql: str = ""


_MULTI_STATEMENT_PATTERN = re.compile(r";\s*\S")  # semicolon followed by more content
_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/|#)")
_WORD_PATTERN = re.compile(r"[A-Za-z_]+")


def validate_sql(sql: str) -> ValidationResult:
    """Validate that `sql` is a single, safe, read-only SELECT statement."""
    if not sql or not sql.strip():
        return ValidationResult(False, "Empty SQL statement.")

    cleaned = sql.strip().rstrip(";").strip()

    # Reject SQL comments outright (common injection / obfuscation vector)
    if _COMMENT_PATTERN.search(cleaned):
        return ValidationResult(False, "SQL comments are not allowed.")

    # Reject multiple statements (statement stacking)
    if _MULTI_STATEMENT_PATTERN.search(sql):
        return ValidationResult(False, "Multiple SQL statements are not allowed.")

    # Must start with SELECT (case-insensitive), ignoring a leading "WITH" CTE
    stripped_upper = cleaned.upper()
    if stripped_upper.startswith("WITH"):
        # Allow read-only CTEs, but the final statement must still resolve to a SELECT
        if " SELECT " not in f" {stripped_upper} ":
            return ValidationResult(False, "CTE must resolve to a SELECT statement.")
    elif not stripped_upper.startswith(settings.ALLOWED_SQL_PREFIX):
        return ValidationResult(False, "Only SELECT statements are permitted.")

    # Scan tokens for forbidden keywords anywhere in the statement
    tokens = {t.upper() for t in _WORD_PATTERN.findall(cleaned)}
    forbidden_hit = tokens.intersection(settings.FORBIDDEN_SQL_KEYWORDS)
    if forbidden_hit:
        return ValidationResult(False, f"Forbidden keyword(s) detected: {', '.join(sorted(forbidden_hit))}")

    return ValidationResult(True, "OK", cleaned_sql=cleaned)


def enforce_row_limit(sql: str, max_rows: int | None = None) -> str:
    """Append a LIMIT clause if the query doesn't already have one."""
    max_rows = max_rows or settings.MAX_SQL_ROWS
    if re.search(r"\bLIMIT\s+\d+\b", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip()} LIMIT {max_rows}"

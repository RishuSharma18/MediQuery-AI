"""
database/db.py
Engine/session management + one-time CSV -> SQLite import.

Two engines are exposed:
- `engine`        : normal read/write engine, used ONLY by the import routine.
- `readonly_engine`: opened in SQLite read-only URI mode, used by everything
                     that executes LLM-generated SQL. This is a hard guarantee
                     against writes even if validation were somehow bypassed.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import settings
from database.models import Base, CSV_COLUMN_MAP
from utils.logger import get_logger

logger = get_logger(__name__)

_DB_URL = f"sqlite:///{settings.DB_PATH}"
_DB_URL_READONLY = f"sqlite:///file:{settings.DB_PATH}?mode=ro&uri=true"

engine = create_engine(_DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_readonly_engine():
    """A fresh read-only engine. Created lazily since the DB file must exist first."""
    return create_engine(_DB_URL_READONLY, echo=False, future=True)


def _table_exists() -> bool:
    return inspect(engine).has_table(settings.TABLE_NAME)


def import_csv_if_needed(force: bool = False) -> int:
    """
    Import healthcare_dataset.csv into SQLite on first run.
    Returns the number of rows in the table after import.
    Safe to call every app startup; it's a no-op if data already exists.
    """
    if _table_exists() and not force:
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {settings.TABLE_NAME}")).scalar()
        logger.info("Patients table already populated with %s rows; skipping import.", count)
        return count

    if not settings.CSV_PATH.exists():
        raise FileNotFoundError(
            f"Expected dataset at {settings.CSV_PATH} but it was not found."
        )

    logger.info("Importing dataset from %s ...", settings.CSV_PATH)
    df = pd.read_csv(settings.CSV_PATH)

    # Normalize column names -> snake_case using the known CSV headers.
    # Any unexpected column is auto-slugified so new datasets don't break import.
    reverse_map = {v: k for k, v in CSV_COLUMN_MAP.items()}
    new_columns = []
    for col in df.columns:
        if col in reverse_map:
            new_columns.append(reverse_map[col])
        else:
            slug = (
                col.strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )
            new_columns.append(slug)
    df.columns = new_columns

    # Normalize text casing (source data has inconsistent capitalization, e.g. "BObby JAckSSon")
    for text_col in ("name", "doctor", "hospital"):
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str).str.strip().str.title()

    for cat_col in ("gender", "blood_type", "medical_condition", "insurance_provider",
                    "admission_type", "medication", "test_results"):
        if cat_col in df.columns:
            df[cat_col] = df[cat_col].astype(str).str.strip()

    # Parse dates
    for date_col in ("date_of_admission", "discharge_date"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.date

    # Drop rows with no name (defensive; source data is generally clean)
    if "name" in df.columns:
        df = df.dropna(subset=["name"])

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    df.to_sql(settings.TABLE_NAME, engine, if_exists="append", index=False)

    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {settings.TABLE_NAME}")).scalar()

    logger.info("Imported %s rows into '%s' table.", count, settings.TABLE_NAME)
    return count


def get_schema_description() -> str:
    """Human-readable schema description injected into the SQL-generation prompt."""
    lines = [f"Table: {settings.TABLE_NAME}", "Columns:"]
    inspector = inspect(engine)
    for col in inspector.get_columns(settings.TABLE_NAME):
        lines.append(f"  - {col['name']} ({col['type']})")
    return "\n".join(lines)
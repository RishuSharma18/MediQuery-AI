"""
tests/test_database.py
Tests the CSV -> SQLite import pipeline and schema description helper.
Uses the real project CSV, so this test does hit disk, but requires no LLM
or network access.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import import_csv_if_needed, get_schema_description
from database import queries

# Ensure the table exists before any test runs, regardless of test execution
# order (import is idempotent/cheap after the first run).
import_csv_if_needed()


def test_import_creates_rows():
    count = import_csv_if_needed()
    assert count > 0


def test_schema_description_mentions_key_columns():
    schema = get_schema_description()
    for col in ("name", "age", "gender", "medical_condition", "doctor"):
        assert col in schema


def test_patient_count_matches_import():
    imported = import_csv_if_needed()
    counted = queries.patient_count()
    assert imported == counted


def test_gender_distribution_not_empty():
    df = queries.gender_distribution()
    assert len(df) > 0


if __name__ == "__main__":
    import inspect
    current_module = sys.modules[__name__]
    test_fns = [f for name, f in inspect.getmembers(current_module, inspect.isfunction)
                if name.startswith("test_")]
    passed, failed = 0, 0
    for fn in test_fns:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__} -- {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
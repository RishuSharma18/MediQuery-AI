"""
database/queries.py
Aggregate queries powering the Analytics Dashboard. Kept separate from
crud.py because these are read-only, aggregate-only, and safe to cache.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from database.db import engine
from config import settings


def _read_sql(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def patient_count() -> int:
    return int(_read_sql(f"SELECT COUNT(*) as c FROM {settings.TABLE_NAME}")["c"].iloc[0])


def doctor_count() -> int:
    return int(_read_sql(f"SELECT COUNT(DISTINCT doctor) as c FROM {settings.TABLE_NAME}")["c"].iloc[0])


def admissions_this_month() -> int:
    return int(_read_sql(f"""
        SELECT COUNT(*) as c FROM {settings.TABLE_NAME}
        WHERE strftime('%Y-%m', date_of_admission) = strftime('%Y-%m', 'now')
    """)["c"].iloc[0])


def total_revenue() -> float:
    return float(_read_sql(f"SELECT COALESCE(SUM(billing_amount),0) as s FROM {settings.TABLE_NAME}")["s"].iloc[0])


def avg_billing() -> float:
    return float(_read_sql(f"SELECT COALESCE(AVG(billing_amount),0) as a FROM {settings.TABLE_NAME}")["a"].iloc[0])


def gender_distribution() -> pd.DataFrame:
    return _read_sql(f"SELECT gender, COUNT(*) as count FROM {settings.TABLE_NAME} GROUP BY gender")


def age_distribution() -> pd.DataFrame:
    return _read_sql(f"SELECT age FROM {settings.TABLE_NAME}")


def disease_distribution() -> pd.DataFrame:
    return _read_sql(f"""
        SELECT medical_condition, COUNT(*) as count FROM {settings.TABLE_NAME}
        GROUP BY medical_condition ORDER BY count DESC
    """)


def department_distribution() -> pd.DataFrame:
    # No explicit "department" column in source data; admission_type is the closest proxy.
    return _read_sql(f"""
        SELECT admission_type, COUNT(*) as count FROM {settings.TABLE_NAME}
        GROUP BY admission_type ORDER BY count DESC
    """)


def insurance_distribution() -> pd.DataFrame:
    return _read_sql(f"""
        SELECT insurance_provider, COUNT(*) as count FROM {settings.TABLE_NAME}
        GROUP BY insurance_provider ORDER BY count DESC
    """)


def blood_group_distribution() -> pd.DataFrame:
    return _read_sql(f"""
        SELECT blood_type, COUNT(*) as count FROM {settings.TABLE_NAME}
        GROUP BY blood_type ORDER BY count DESC
    """)


def doctor_workload(top_n: int = 10) -> pd.DataFrame:
    return _read_sql(f"""
        SELECT doctor, COUNT(*) as appointments FROM {settings.TABLE_NAME}
        GROUP BY doctor ORDER BY appointments DESC LIMIT {top_n}
    """)


def admissions_over_time() -> pd.DataFrame:
    return _read_sql(f"""
        SELECT strftime('%Y-%m', date_of_admission) as month, COUNT(*) as count
        FROM {settings.TABLE_NAME}
        GROUP BY month ORDER BY month
    """)


def test_results_distribution() -> pd.DataFrame:
    return _read_sql(f"""
        SELECT test_results, COUNT(*) as count FROM {settings.TABLE_NAME}
        GROUP BY test_results ORDER BY count DESC
    """)
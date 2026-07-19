"""
database/models.py
SQLAlchemy ORM model matching the healthcare_dataset.csv schema.
Column names are normalized to snake_case for SQL-friendliness while the
original CSV headers are preserved in `CSV_COLUMN_MAP` for import purposes.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Maps normalized DB column name -> original CSV header
CSV_COLUMN_MAP = {
    "name": "Name",
    "age": "Age",
    "gender": "Gender",
    "blood_type": "Blood Type",
    "medical_condition": "Medical Condition",
    "date_of_admission": "Date of Admission",
    "doctor": "Doctor",
    "hospital": "Hospital",
    "insurance_provider": "Insurance Provider",
    "billing_amount": "Billing Amount",
    "room_number": "Room Number",
    "admission_type": "Admission Type",
    "discharge_date": "Discharge Date",
    "medication": "Medication",
    "test_results": "Test Results",
}


class Patient(Base):
    """One row per hospital admission record."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    age = Column(Integer, index=True)
    gender = Column(String, index=True)
    blood_type = Column(String, index=True)
    medical_condition = Column(String, index=True)
    date_of_admission = Column(Date, index=True)
    doctor = Column(String, index=True)
    hospital = Column(String)
    insurance_provider = Column(String, index=True)
    billing_amount = Column(Float)
    room_number = Column(Integer)
    admission_type = Column(String, index=True)
    discharge_date = Column(Date)
    medication = Column(String)
    test_results = Column(String, index=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
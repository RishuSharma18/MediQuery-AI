import pandas as pd
from sqlalchemy import create_engine

CSV_PATH = "data/healthcare_dataset.csv"

DATABASE_PATH = "sqlite:///data/hospital.db"

engine = create_engine(DATABASE_PATH)

print("Loading CSV...")

df = pd.read_csv(CSV_PATH)

print(df.head())

table_name = "patients"

df.to_sql(
    table_name,
    engine,
    if_exists="replace",
    index=False
)

print()

print("Database Created Successfully!")

print()

print(f"Total Rows : {len(df)}")
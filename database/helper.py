import pandas as pd
import sqlite3

connection = sqlite3.connect("data/hospital.db")


def run_query(query):

    return pd.read_sql(query, connection)
import streamlit as st
from database.helper import run_query

st.set_page_config(
    page_title="MediQuery AI",
    layout="wide"
)

st.title("🏥 MediQuery AI")

st.subheader("Patient Database")

patients = run_query(
    "SELECT * FROM patients LIMIT 20"
)

st.dataframe(patients)

total = run_query(
    "SELECT COUNT(*) AS Total FROM patients"
)

st.metric(
    "Patients",
    int(total.iloc[0]["Total"])
)
"""
pages/2_Dashboard.py
Analytics Dashboard: hospital-wide metrics and distributions via Plotly.
"""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from database import queries
from config import settings

st.set_page_config(page_title=f"Dashboard - {settings.APP_TITLE}", page_icon="📊", layout="wide")

st.title("📊 Analytics Dashboard")
st.caption("Hospital-wide statistics computed live from the patient records database.")

# --- Top-level metrics ---
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Patients", f"{queries.patient_count():,}")
m2.metric("Doctors", queries.doctor_count())
m3.metric("Admissions (this month)", queries.admissions_this_month())
m4.metric("Total Revenue", f"${queries.total_revenue():,.0f}")
m5.metric("Avg. Billing / Patient", f"${queries.avg_billing():,.0f}")

st.divider()

# --- Row 1: Gender + Age ---
c1, c2 = st.columns(2)
with c1:
    st.subheader("Gender Distribution")
    df = queries.gender_distribution()
    fig = px.pie(df, names="gender", values="count", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Age Distribution")
    df = queries.age_distribution()
    fig = px.histogram(df, x="age", nbins=30)
    fig.update_layout(bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)

# --- Row 2: Disease + Department (admission type) ---
c3, c4 = st.columns(2)
with c3:
    st.subheader("Medical Condition Distribution")
    df = queries.disease_distribution()
    fig = px.bar(df, x="medical_condition", y="count", color="medical_condition")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Admission Type Distribution")
    df = queries.department_distribution()
    fig = px.bar(df, x="admission_type", y="count", color="admission_type")
    st.plotly_chart(fig, use_container_width=True)

# --- Row 3: Insurance + Blood Group ---
c5, c6 = st.columns(2)
with c5:
    st.subheader("Insurance Provider Distribution")
    df = queries.insurance_distribution()
    fig = px.pie(df, names="insurance_provider", values="count", hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Blood Group Distribution")
    df = queries.blood_group_distribution()
    fig = px.bar(df, x="blood_type", y="count", color="blood_type")
    st.plotly_chart(fig, use_container_width=True)

# --- Row 4: Doctor workload + Admissions over time ---
c7, c8 = st.columns(2)
with c7:
    st.subheader("Top 10 Doctors by Patient Load")
    df = queries.doctor_workload(top_n=10)
    fig = px.bar(df, x="appointments", y="doctor", orientation="h")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

with c8:
    st.subheader("Admissions Over Time")
    df = queries.admissions_over_time()
    fig = px.line(df, x="month", y="count", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- Row 5: Test results ---
st.subheader("Test Results Distribution")
df = queries.test_results_distribution()
fig = px.bar(df, x="test_results", y="count", color="test_results")
st.plotly_chart(fig, use_container_width=True)
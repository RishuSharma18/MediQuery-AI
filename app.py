"""
app.py
MediQuery AI -- main entry point and Home page.
Run with: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config import settings
from database.db import import_csv_if_needed
from database import queries
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Setting up database (first run only)...")
def _init_database():
    return import_csv_if_needed()


def _inject_css():
    st.markdown(
        """
        <style>
        .metric-card {
            background: #ffffff10;
            border: 1px solid #ffffff20;
            border-radius: 12px;
            padding: 1rem 1.2rem;
        }
        .status-ok { color: #22c55e; font-weight: 600; }
        .status-warn { color: #f59e0b; font-weight: 600; }
        .status-err { color: #ef4444; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _sidebar():
    with st.sidebar:
        st.markdown(f"## 🏥 {settings.APP_TITLE}")
        st.caption("Multi-Agent Hospital Intelligence System")
        st.divider()
        st.markdown("**Backend status**")
        try:
            import requests
            requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
            st.markdown('<span class="status-ok">● Ollama reachable</span>', unsafe_allow_html=True)
        except Exception:
            st.markdown('<span class="status-err">● Ollama not reachable</span>', unsafe_allow_html=True)
            st.caption("Run `ollama serve` and pull a model to enable AI features.")
        st.divider()
        st.caption("Use the pages in this sidebar to navigate: Chat, Dashboard, "
                    "Patient Explorer, Documents, SQL Logs.")


def main():
    _inject_css()
    row_count = _init_database()
    _sidebar()

    st.title(f"🏥 {settings.APP_TITLE}")
    st.subheader("Multi-Agent Hospital Intelligence System")
    st.write(
        "Ask questions in plain English about patient records or hospital policy. "
        "MediQuery AI automatically figures out whether it needs to query the database, "
        "search policy documents, or both."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", f"{queries.patient_count():,}")
    with col2:
        st.metric("Doctors", queries.doctor_count())
    with col3:
        st.metric("Admissions (this month)", queries.admissions_this_month())
    with col4:
        st.metric("Total Billing", f"${queries.total_revenue():,.0f}")

    st.divider()

    st.markdown("### Try asking things like:")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    with ex_col1:
        st.info("**SQL**\n\nShow all diabetic patients above 60")
    with ex_col2:
        st.info("**RAG**\n\nWhat is the ICU visitor policy?")

    st.page_link("pages/1_Chat.py", label="➡️ Go to AI Chat", icon="💬")

    st.divider()
    st.caption(
        f"Dataset loaded: {row_count:,} patient records | "
        f"LLM backend: {settings.LLM_PROVIDER} ({settings.OLLAMA_MODEL if settings.LLM_PROVIDER=='ollama' else settings.OPENAI_MODEL})"
    )


if __name__ == "__main__":
    main()
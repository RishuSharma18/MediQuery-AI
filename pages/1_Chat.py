"""
pages/1_Chat.py
ChatGPT-style conversational interface backed by the orchestrator agent.
"""
from __future__ import annotations

import streamlit as st

from agents.orchestrator import handle_query
from config import settings

st.set_page_config(page_title=f"Chat - {settings.APP_TITLE}", page_icon="💬", layout="wide")

st.title("💬 AI Chat")
st.caption("Ask about patient records, hospital policies, or both. MediQuery AI figures out how to answer.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {role, content, meta}

# Render conversation history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        meta = msg.get("meta")
        if meta:
            with st.expander("🔎 Agent execution details", expanded=False):
                st.markdown(f"**Route:** `{meta.get('category')}`  |  "
                            f"**Time:** {meta.get('duration_seconds')}s  |  "
                            f"**Reasoning:** {meta.get('reasoning')}")
                if meta.get("sql"):
                    st.markdown("**SQL executed:**")
                    st.code(meta["sql"], language="sql")
                if meta.get("dataframe") is not None and not meta["dataframe"].empty:
                    st.markdown("**Query result:**")
                    st.dataframe(meta["dataframe"], use_container_width=True)
                if meta.get("retrieved"):
                    st.markdown("**Retrieved policy excerpts:**")
                    for r in meta["retrieved"]:
                        st.markdown(f"*Source: {r.source.replace('_', ' ')} (distance={r.score:.3f})*")
                        st.text(r.text[:400] + ("..." if len(r.text) > 400 else ""))
                if meta.get("error"):
                    st.warning(f"Note: {meta['error']}")

# Chat input
user_question = st.chat_input("Ask a question about patients or hospital policy...")

if user_question:
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = handle_query(user_question)
        st.markdown(result.answer)
        with st.expander("🔎 Agent execution details", expanded=False):
            st.markdown(f"**Route:** `{result.category}`  |  "
                        f"**Time:** {result.duration_seconds}s  |  "
                        f"**Reasoning:** {result.reasoning}")
            if result.sql:
                st.markdown("**SQL executed:**")
                st.code(result.sql, language="sql")
            if not result.dataframe.empty:
                st.markdown("**Query result:**")
                st.dataframe(result.dataframe, use_container_width=True)
            if result.retrieved:
                st.markdown("**Retrieved policy excerpts:**")
                for r in result.retrieved:
                    st.markdown(f"*Source: {r.source.replace('_', ' ')} (distance={r.score:.3f})*")
                    st.text(r.text[:400] + ("..." if len(r.text) > 400 else ""))
            if result.error:
                st.warning(f"Note: {result.error}")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result.answer,
        "meta": {
            "category": result.category,
            "reasoning": result.reasoning,
            "duration_seconds": result.duration_seconds,
            "sql": result.sql,
            "dataframe": result.dataframe,
            "retrieved": result.retrieved,
            "error": result.error,
        },
    })

col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        st.rerun()
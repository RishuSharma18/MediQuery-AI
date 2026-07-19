"""
agents/sql_agent.py
Converts a natural-language question into SQL, safely executes it, and
summarizes the result in plain English.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from database.db import get_schema_description
from services.llm import llm_client, LLMError
from services.sql_executor import execute_sql, SQLExecutionError
from utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "sql_prompt.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


@dataclass
class SQLAgentResult:
    success: bool
    question: str
    sql: str = ""
    dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    answer: str = ""
    error: str = ""


def _clean_llm_sql(raw: str) -> str:
    """Strip markdown fences / stray prose the LLM might add despite instructions."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("sql"):
            cleaned = cleaned[3:]
    # If the model added prose before/after, keep only the first SELECT/WITH ... to end
    upper = cleaned.upper()
    start = min(
        (upper.find(kw) for kw in ("SELECT", "WITH") if upper.find(kw) != -1),
        default=0,
    )
    return cleaned[start:].strip()


def generate_sql(question: str) -> str:
    schema = get_schema_description()
    prompt = _PROMPT_TEMPLATE.format(schema=schema, question=question)
    raw = llm_client.chat(
        system_prompt="You are an expert, safety-conscious SQL generator. Output SQL only.",
        user_prompt=prompt,
        temperature=0.0,
    )
    return _clean_llm_sql(raw)


def summarize_result(question: str, sql: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "No matching records were found for this query."

    preview = df.head(20).to_markdown(index=False)
    prompt = (
        f"User question: {question}\n\n"
        f"SQL executed: {sql}\n\n"
        f"Result ({len(df)} row(s), showing up to 20):\n{preview}\n\n"
        "Write a concise, natural-language answer to the user's question based on this "
        "result. Mention specific numbers/names where relevant. Do not mention SQL or "
        "databases in your answer -- just answer as a helpful hospital assistant."
    )
    try:
        return llm_client.chat(
            system_prompt="You are a helpful hospital data assistant.",
            user_prompt=prompt,
            temperature=0.2,
        )
    except LLMError as e:
        logger.warning("Summary generation failed, falling back to raw stats: %s", e)
        return f"Found {len(df)} matching record(s). See the table below for details."


def run_sql_agent(question: str) -> SQLAgentResult:
    """End-to-end: NL -> SQL -> validate/execute -> NL summary."""
    try:
        sql = generate_sql(question)
    except LLMError as e:
        return SQLAgentResult(success=False, question=question, error=str(e))

    try:
        df = execute_sql(sql, question=question)
    except SQLExecutionError as e:
        return SQLAgentResult(success=False, question=question, sql=sql, error=str(e))

    answer = summarize_result(question, sql, df)
    return SQLAgentResult(success=True, question=question, sql=sql, dataframe=df, answer=answer)
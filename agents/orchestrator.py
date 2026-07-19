"""
agents/orchestrator.py
Top-level entry point for every user question. Classifies it, routes it to
the SQL Agent or the RAG Agent, and returns one consistent response shape
the Chat page can render either way.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd

from agents.classifier import classify_query
from agents.sql_agent import run_sql_agent
from agents.rag_agent import run_rag_agent, RetrievedChunk
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OrchestratorResult:
    success: bool
    question: str
    category: str
    answer: str
    sql: str = ""
    dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    reasoning: str = ""
    duration_seconds: float = 0.0
    error: str = ""


def handle_query(question: str) -> OrchestratorResult:
    """Classify and route a user question, with graceful error handling throughout."""
    start = time.time()
    question = (question or "").strip()

    if not question:
        return OrchestratorResult(
            success=False, question=question, category="NONE",
            answer="Please enter a question.", error="Empty question.",
        )

    try:
        classification = classify_query(question)
    except Exception as e:
        logger.error("Classification failed unexpectedly: %s", e)
        classification = {"category": "SQL", "reasoning": "classification error, defaulted to SQL"}

    category = classification.get("category", "SQL")
    reasoning = classification.get("reasoning", "")
    logger.info("Routed question to %s | reasoning=%s | question=%s", category, reasoning, question)

    try:
        if category == "SQL":
            result = run_sql_agent(question)
            out = OrchestratorResult(
                success=result.success, question=question, category=category,
                answer=result.answer or result.error, sql=result.sql,
                dataframe=result.dataframe, reasoning=reasoning, error=result.error,
            )
        else:  # RAG
            result = run_rag_agent(question)
            out = OrchestratorResult(
                success=result.success, question=question, category=category,
                answer=result.answer or result.error, retrieved=result.retrieved,
                reasoning=reasoning, error=result.error,
            )
    except Exception as e:
        logger.exception("Unhandled agent failure for question: %s", question)
        out = OrchestratorResult(
            success=False, question=question, category=category,
            answer="Something went wrong while processing your question. Please try again "
                   "or rephrase it. If this keeps happening, check that Ollama is running.",
            reasoning=reasoning, error=str(e),
        )

    out.duration_seconds = round(time.time() - start, 2)
    return out
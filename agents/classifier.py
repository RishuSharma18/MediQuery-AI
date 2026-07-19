"""
agents/classifier.py
Classifies an incoming user question as SQL or RAG.

Primary path: ask the LLM for a structured classification.
Fallback path: if the LLM is unreachable or returns unparsable output, fall
back to a simple keyword heuristic so the app degrades gracefully instead of
crashing.
"""
from __future__ import annotations

from pathlib import Path

from services.llm import llm_client, LLMError
from utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "orchestrator_prompt.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")

_RAG_KEYWORDS = (
    "policy", "protocol", "procedure", "guideline", "sop", "rule", "rules",
    "process", "visitor", "evacuation", "privacy", "rights",
    "infection control", "pharmacy policy",
)


def _heuristic_classify(question: str) -> dict:
    """Simple fallback used only if the LLM is unreachable: if the question
    mentions policy-related words, route to RAG, otherwise default to SQL."""
    q = question.lower()
    category = "RAG" if any(k in q for k in _RAG_KEYWORDS) else "SQL"
    return {"category": category, "reasoning": "heuristic keyword fallback (LLM unavailable)"}


def classify_query(question: str) -> dict:
    """Returns {"category": "SQL"|"RAG", "reasoning": str}."""
    prompt = _PROMPT_TEMPLATE.format(question=question)
    try:
        result = llm_client.chat_json(
            system_prompt="You are a precise query classification system. Respond with JSON only.",
            user_prompt=prompt,
        )
        category = str(result.get("category", "")).upper().strip()
        if category not in ("SQL", "RAG"):
            raise ValueError(f"Unexpected category from LLM: {category}")
        result["category"] = category
        return result
    except Exception as e:
        logger.warning("Classifier LLM path failed (%s); using heuristic fallback.", e)
        return _heuristic_classify(question)
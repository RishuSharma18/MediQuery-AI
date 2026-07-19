"""
services/llm.py
Thin LLM client. Defaults to Ollama (local, free, no API key). If OPENAI_API_KEY
is set and LLM_PROVIDER=openai in .env, it transparently switches to OpenAI
instead -- nothing else in the codebase needs to change.
"""
from __future__ import annotations

import json
from typing import Optional

import requests

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


class LLMClient:
    """Unified chat-completion interface used by every agent."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return self._chat_openai(system_prompt, user_prompt, temperature)
        return self._chat_ollama(system_prompt, user_prompt, temperature)

    # --- Ollama backend (default: local, free) ---
    def _chat_ollama(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            resp = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise LLMError(
                f"Could not reach Ollama at {settings.OLLAMA_BASE_URL}. "
                f"Is it running? Start it with `ollama serve` and make sure "
                f"you've pulled the model with `ollama pull {settings.OLLAMA_MODEL}`."
            ) from e
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Ollama request failed: {e}") from e

        data = resp.json()
        content = data.get("message", {}).get("content", "")
        if not content:
            raise LLMError(f"Ollama returned an empty response: {data}")
        return content.strip()

    # --- OpenAI backend (optional, only if user later provides a key) ---
    def _chat_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError("openai package not installed. Run: pip install openai") from e

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as e:
            raise LLMError(f"OpenAI request failed: {e}") from e
        return resp.choices[0].message.content.strip()

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> dict:
        """Convenience wrapper that asks for and parses a strict JSON response."""
        raw = self.chat(system_prompt, user_prompt, temperature=temperature)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON from LLM output: %s | raw=%s", e, raw)
            raise LLMError(f"LLM did not return valid JSON: {raw[:300]}") from e


llm_client = LLMClient()
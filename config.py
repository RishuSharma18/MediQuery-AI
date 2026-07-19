"""
config.py
Central configuration for MediQuery AI.
All paths and tunables are resolved relative to the project root so the
app can be run from any working directory.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (folder containing this file)
ROOT_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(ROOT_DIR / ".env")


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


class Settings:
    """Typed application settings, loaded once at import time."""

    # --- Paths ---
    ROOT_DIR: Path = ROOT_DIR
    DATA_DIR: Path = ROOT_DIR / "data"
    CSV_PATH: Path = DATA_DIR / "healthcare_dataset.csv"
    DB_PATH: Path = ROOT_DIR / _env("DB_PATH", "data/hospital.db")
    DOCS_DIR: Path = ROOT_DIR / _env("DOCS_DIR", "docs")
    VECTORSTORE_DIR: Path = ROOT_DIR / _env("VECTORSTORE_DIR", "vectorstore")
    FAISS_INDEX_PATH: Path = VECTORSTORE_DIR / "faiss_index.bin"
    FAISS_META_PATH: Path = VECTORSTORE_DIR / "faiss_meta.pkl"
    LOGS_DIR: Path = ROOT_DIR / _env("LOGS_DIR", "logs")
    APP_LOG_PATH: Path = LOGS_DIR / "app.log"

    # --- LLM backend (local, free, no API key required) ---
    LLM_PROVIDER: str = _env("LLM_PROVIDER", "ollama")  # "ollama" or "openai"
    OLLAMA_BASE_URL: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = _env("OLLAMA_MODEL", "llama3.1:8b")
    OLLAMA_TIMEOUT: int = int(_env("OLLAMA_TIMEOUT", "120"))

    # Optional: only used if LLM_PROVIDER=openai and a key is supplied later
    OPENAI_API_KEY: str = _env("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = _env("OPENAI_MODEL", "gpt-4o-mini")

    # --- Embeddings (local, free, no API key required) ---
    EMBEDDING_MODEL: str = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = 384  # matches all-MiniLM-L6-v2

    # --- RAG tuning ---
    CHUNK_SIZE: int = int(_env("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(_env("CHUNK_OVERLAP", "120"))
    TOP_K: int = int(_env("TOP_K", "4"))

    # --- SQL safety ---
    ALLOWED_SQL_PREFIX: str = "SELECT"
    FORBIDDEN_SQL_KEYWORDS = (
        "DELETE", "DROP", "UPDATE", "INSERT", "ALTER",
        "TRUNCATE", "ATTACH", "DETACH", "PRAGMA", "REPLACE",
        "CREATE", "GRANT", "REVOKE", "VACUUM",
    )
    MAX_SQL_ROWS: int = int(_env("MAX_SQL_ROWS", "500"))

    # --- App ---
    APP_TITLE: str = "MediQuery AI"
    TABLE_NAME: str = "patients"


settings = Settings()

# Ensure required directories exist at import time
for _dir in (settings.DATA_DIR, settings.DOCS_DIR, settings.VECTORSTORE_DIR, settings.LOGS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
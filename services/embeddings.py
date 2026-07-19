"""
services/embeddings.py
Local, free embeddings via Sentence-Transformers (no API key required).
The model is loaded lazily and cached so Streamlit reruns don't reload it.
"""
from __future__ import annotations

import numpy as np

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model '%s' (first call only)...", settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts. Returns an (N, EMBEDDING_DIM) float32 array."""
    if not texts:
        return np.empty((0, settings.EMBEDDING_DIM), dtype="float32")
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.astype("float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string. Returns a (1, EMBEDDING_DIM) float32 array."""
    return embed_texts([query])
"""
services/vectorstore.py
FAISS-backed vector store for hospital policy document chunks.
Persists the index + metadata to disk so it only needs to be built once.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass, field

import faiss
import numpy as np

from config import settings
from services.embeddings import embed_texts, embed_query
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """Simple flat-L2 FAISS index with a parallel Python list of chunk metadata."""

    def __init__(self):
        self.index: faiss.Index | None = None
        self.chunks: list[Chunk] = []

    def build(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("Cannot build a vector store from zero chunks.")
        vectors = embed_texts([c.text for c in chunks])
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        self.index = index
        self.chunks = chunks
        logger.info("Built FAISS index with %d chunks.", len(chunks))

    def save(self) -> None:
        if self.index is None:
            raise RuntimeError("No index to save. Call build() first.")
        faiss.write_index(self.index, str(settings.FAISS_INDEX_PATH))
        with open(settings.FAISS_META_PATH, "wb") as f:
            pickle.dump(self.chunks, f)
        logger.info("Saved FAISS index to %s", settings.FAISS_INDEX_PATH)

    def load(self) -> bool:
        """Load a previously-saved index. Returns False if none exists yet."""
        if not settings.FAISS_INDEX_PATH.exists() or not settings.FAISS_META_PATH.exists():
            return False
        self.index = faiss.read_index(str(settings.FAISS_INDEX_PATH))
        with open(settings.FAISS_META_PATH, "rb") as f:
            self.chunks = pickle.load(f)
        logger.info("Loaded FAISS index with %d chunks.", len(self.chunks))
        return True

    def exists_on_disk(self) -> bool:
        return settings.FAISS_INDEX_PATH.exists() and settings.FAISS_META_PATH.exists()

    def search(self, query: str, top_k: int | None = None) -> list[tuple[Chunk, float]]:
        if self.index is None:
            raise RuntimeError("Vector store not loaded. Call load() or build() first.")
        top_k = top_k or settings.TOP_K
        query_vec = embed_query(query)
        distances, indices = self.index.search(query_vec, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], float(dist)))
        return results


vector_store = VectorStore()
"""
agents/rag_agent.py
Retrieval-Augmented Generation over hospital policy documents.

Pipeline: generate policy PDFs if missing -> extract text -> chunk -> embed ->
FAISS index -> retrieve top-k chunks for a query -> generate a grounded answer
with document citations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from config import settings
from services.doc_generator import generate_policy_documents_if_needed
from services.vectorstore import vector_store, Chunk
from services.llm import llm_client, LLMError
from utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "rag_prompt.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


@dataclass
class RAGAgentResult:
    success: bool
    question: str
    answer: str = ""
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    error: str = ""


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, source: str) -> list[Chunk]:
    """Simple fixed-size sliding-window chunker with overlap."""
    size, overlap = settings.CHUNK_SIZE, settings.CHUNK_OVERLAP
    text = " ".join(text.split())  # normalize whitespace
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = start + size
        piece = text[start:end]
        if piece.strip():
            chunks.append(Chunk(text=piece.strip(), source=source, chunk_id=chunk_id))
            chunk_id += 1
        start += size - overlap
    return chunks


def build_index(force: bool = False) -> int:
    """
    Build (or rebuild) the FAISS index from every PDF in settings.DOCS_DIR.
    Auto-generates policy PDFs first if the docs folder is empty.
    Returns the number of chunks indexed.
    """
    generate_policy_documents_if_needed(force=False)

    pdf_paths = sorted(settings.DOCS_DIR.glob("*.pdf"))
    if not pdf_paths:
        raise RuntimeError(f"No PDFs found in {settings.DOCS_DIR} even after generation attempt.")

    all_chunks: list[Chunk] = []
    for pdf_path in pdf_paths:
        try:
            text = _extract_pdf_text(pdf_path)
        except Exception as e:
            logger.error("Failed to read %s: %s", pdf_path.name, e)
            continue
        chunks = _chunk_text(text, source=pdf_path.stem)
        all_chunks.extend(chunks)

    vector_store.build(all_chunks)
    vector_store.save()
    return len(all_chunks)


def ensure_index_ready() -> None:
    """Load the index from disk, building it the first time if necessary."""
    if vector_store.index is not None:
        return
    if vector_store.exists_on_disk():
        vector_store.load()
    else:
        logger.info("No existing FAISS index found; building one now (first run)...")
        build_index()


def retrieve(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    ensure_index_ready()
    results = vector_store.search(question, top_k=top_k)
    return [RetrievedChunk(text=c.text, source=c.source, score=score) for c, score in results]


def generate_answer(question: str, retrieved: list[RetrievedChunk]) -> str:
    if not retrieved:
        return "I couldn't find any relevant policy information to answer this question."

    context = "\n\n".join(
        f"[{r.source.replace('_', ' ')}]\n{r.text}" for r in retrieved
    )
    prompt = _PROMPT_TEMPLATE.format(context=context, question=question)
    return llm_client.chat(
        system_prompt="You are a grounded, careful hospital policy assistant. Only use the "
                       "provided excerpts; do not invent policy details.",
        user_prompt=prompt,
        temperature=0.1,
    )


def run_rag_agent(question: str, top_k: int | None = None) -> RAGAgentResult:
    """End-to-end: retrieve relevant chunks -> generate a grounded, cited answer."""
    try:
        retrieved = retrieve(question, top_k=top_k)
    except Exception as e:
        logger.error("Retrieval failed: %s", e)
        return RAGAgentResult(success=False, question=question, error=str(e))

    try:
        answer = generate_answer(question, retrieved)
    except LLMError as e:
        return RAGAgentResult(success=False, question=question, retrieved=retrieved, error=str(e))

    return RAGAgentResult(success=True, question=question, answer=answer, retrieved=retrieved)
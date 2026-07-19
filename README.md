# MediQuery AI — Multi-Agent Hospital Intelligence System

Ask questions in plain English about patient records or hospital policy. MediQuery AI
automatically figures out whether it needs to query the database (SQL), search policy
documents (RAG), or both (Hybrid) — powered entirely by free, local tools (Ollama + 
Sentence-Transformers). No API key required.

## Architecture

User question
│
▼
Orchestrator ──► Classifier (SQL / RAG / HYBRID)
│
├── SQL ────► NL→SQL (Ollama) → Safety Validator → Read-only SQLite → NL Summary
├── RAG ────► FAISS retrieval (Sentence-Transformers) → Grounded Answer (Ollama)
└── HYBRID ─► Both above → Response Synthesizer → Combined Answer

## Setup

1. Install [Ollama](https://ollama.com) and pull a model:
```bash
   ollama pull phi3        # or llama3.1:8b for higher quality
```
2. Create a virtual environment and install dependencies:
```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and set `OLLAMA_MODEL` to match whatever you pulled.
4. Place `healthcare_dataset.csv` in `data/`.
5. Run the app:
```bash
   streamlit run app.py
```

First run will automatically: import the CSV into SQLite, generate 12 policy PDFs, and
build the FAISS vector index. Subsequent runs skip all of that and just load what exists.

## Project Structure

- `agents/` — classifier, SQL agent, RAG agent, hybrid agent, orchestrator, response synthesizer
- `services/` — LLM client (Ollama), embeddings, FAISS vector store, SQL executor, doc generator
- `database/` — SQLAlchemy models, CSV import, CRUD, dashboard queries
- `pages/` — Streamlit pages (Chat, Dashboard, Patient Explorer, Documents, SQL Logs)
- `prompts/` — LLM prompt templates
- `utils/` — logging, SQL safety validator

## Safety

All LLM-generated SQL passes through a strict validator before execution: only single
`SELECT` statements are allowed, comments and stacked statements are rejected, and
execution happens over a read-only SQLite connection as a second layer of defense.

## Testing

```bash
python tests/test_validators.py
python tests/test_database.py
```

## Notes / Next Steps

This is a scoped one-day MVP. Natural extensions: role-based login, theme switching,
feedback system, OpenAI as an alternate LLM backend (already supported via `.env`,
just needs a key), and deployment configs for Streamlit Cloud/Render/Railway.
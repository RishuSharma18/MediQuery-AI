# 🏥 MediQuery AI — Multi-Agent Hospital Intelligence System

MediQuery AI is an AI-powered application that lets hospital staff ask questions in **plain
English** about patient records or hospital policy — through a single chat interface.

An **Orchestrator Agent** reads every question and decides which specialist should answer it:

- **SQL Agent** — for questions about structured patient data (diagnoses, ages, doctors,
  billing, admissions, etc.)
- **RAG Agent** — for questions about hospital policies and procedures (visitor rules, ICU
  guidelines, discharge process, fire safety, etc.)

Everything runs **locally and for free** — no OpenAI key required. The LLM is powered by
[Ollama](https://ollama.com), and embeddings run locally via Sentence-Transformers.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
4. [Running the App](#running-the-app)
5. [How Each Piece Works](#how-each-piece-works)
6. [Safety: How We Stop Dangerous SQL](#safety-how-we-stop-dangerous-sql)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Future Improvements](#future-improvements)
10. [License](#license)

---

## How It Works

```
                        User types a question in the Chat page
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Orchestrator   │
                              │     Agent       │
                              │                 │
                              │  "Does this     │
                              │   need database │
                              │   facts, or     │
                              │   policy        │
                              │   knowledge?"   │
                              └────────┬────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
             ┌───────────────┐                   ┌───────────────┐
             │   SQL Agent    │                   │   RAG Agent    │
             │                │                   │                │
             │ English → SQL  │                   │ Search policy  │
             │ → validate →   │                   │ PDFs → build   │
             │ run safely →   │                   │ grounded       │
             │ summarize      │                   │ answer         │
             └───────┬────────┘                   └───────┬────────┘
                     │                                     │
                     └──────────────────┬──────────────────┘
                                         ▼
                              Answer shown in the Chat UI
```

**Example questions and where they go:**

| Question | Routed to | Why |
|---|---|---|
| "Show all diabetic patients above 60" | SQL Agent | Needs to query structured patient records |
| "How many patients were admitted this month?" | SQL Agent | Needs a database count |
| "What is the ICU visitor policy?" | RAG Agent | Needs a written policy document |
| "Explain the discharge process" | RAG Agent | Needs a written SOP document |

Every question goes down **exactly one path** — there's no merging of answers, which keeps
the system simple and easy to reason about.

---

## Project Structure

```
MediQuery-AI/
│
├── app.py                    # Streamlit entry point — the Home page
├── config.py                 # All settings in one place (paths, model names, safety limits)
├── .env                       # Your local settings (not committed to git)
├── .env.example                # Template for .env
├── requirements.txt
├── README.md
│
├── data/
│   ├── healthcare_dataset.csv    # Your source data (you provide this)
│   └── hospital.db                # Auto-generated SQLite database (built from the CSV)
│
├── docs/                      # Auto-generated: 12 realistic hospital policy PDFs
│                               #   (Visitor Policy, ICU Guidelines, Discharge SOP, etc.)
│                               #   This is the RAG Agent's source material.
│
├── vectorstore/                # Auto-generated: FAISS search index built from docs/
│   ├── faiss_index.bin
│   └── faiss_meta.pkl
│
├── logs/
│   └── app.log                 # Running log of everything the app does
│
├── database/
│   ├── models.py                # Defines the "patients" table structure
│   ├── db.py                     # Imports the CSV into SQLite, exposes schema info
│   └── queries.py                 # Aggregate queries that power the Dashboard charts
│
├── services/
│   ├── llm.py                     # Talks to Ollama (or OpenAI, if you switch later)
│   ├── embeddings.py                # Turns text into vectors (Sentence-Transformers)
│   ├── vectorstore.py                 # FAISS-based semantic search
│   ├── doc_generator.py                # Writes the 12 policy PDFs to docs/
│   └── sql_executor.py                  # Safely validates + runs SQL, read-only
│
├── agents/
│   ├── classifier.py            # Decides: does this question need SQL or RAG?
│   ├── sql_agent.py              # English → SQL → safe execution → English answer
│   ├── rag_agent.py               # Search PDFs → grounded English answer
│   └── orchestrator.py             # Ties classifier + both agents together
│
├── prompts/
│   ├── orchestrator_prompt.txt      # Prompt used by the classifier
│   ├── sql_prompt.txt                # Prompt used by the SQL Agent
│   └── rag_prompt.txt                 # Prompt used by the RAG Agent
│
├── pages/
│   └── 2_Dashboard.py           # Analytics charts (Plotly), no AI involved
│
├── utils/
│   ├── logger.py                # Shared logging used across every file
│   └── validators.py              # The safety gate — blocks dangerous SQL
│
└── tests/
    ├── test_validators.py         # Confirms dangerous SQL is always rejected
    └── test_database.py            # Confirms the CSV import works correctly
```

Note: `pages/1_Chat.py` also exists — Streamlit's multipage system reads every file inside
`pages/` automatically and lists them in the sidebar in filename order (`1_Chat.py` before
`2_Dashboard.py`), so the Home page (`app.py`) always appears first.

---

## Setup Instructions

### 1. Install Ollama (free, local AI — no API key)

Download from [ollama.com](https://ollama.com) and install it. Then pull a model:

```bash
ollama pull phi3
```

`phi3` (~2.3 GB) is a good beginner choice — small and fast. For higher-quality answers
later, you can also try `llama3.1:8b` (~4.7 GB).

Confirm it's running:
```bash
ollama list
```
You should see your model listed.

### 2. Set up the Python environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy the example file and adjust if needed:
```bash
cp .env.example .env
```

Make sure `OLLAMA_MODEL` in `.env` matches whatever model you pulled, e.g.:
```
OLLAMA_MODEL=phi3
```

### 4. Add your dataset

Place `healthcare_dataset.csv` inside the `data/` folder.

---

## Running the App

```bash
streamlit run app.py
```

This opens `http://localhost:8501` in your browser. **On first run**, the app automatically:

1. Imports your CSV into a local SQLite database (`data/hospital.db`)
2. Generates 12 realistic hospital policy PDFs into `docs/`
3. Builds a FAISS search index from those PDFs into `vectorstore/`

All three steps are **skipped automatically on every future run** — they only happen once,
the first time.

---

## How Each Piece Works

### Orchestrator Agent (`agents/orchestrator.py` + `agents/classifier.py`)

Every question passes through here first. The classifier sends your question to the LLM
with a short prompt asking it to pick `"SQL"` or `"RAG"`. If the LLM can't be reached (e.g.
Ollama isn't running), a simple keyword-based fallback kicks in instead — so the app never
crashes just because the AI backend is temporarily down.

### SQL Agent (`agents/sql_agent.py`)

1. Takes your question and the database schema, and asks the LLM to write a SQL `SELECT`
   statement that answers it.
2. Passes that SQL through the safety validator (see below).
3. Runs it against a **read-only** database connection.
4. Sends the result back to the LLM and asks it to summarize it in plain English.

### RAG Agent (`agents/rag_agent.py`)

RAG stands for **Retrieval-Augmented Generation** — instead of letting the AI make things up,
we force it to answer using only real document excerpts:

1. The 12 policy PDFs are split into overlapping ~800-character chunks.
2. Each chunk is converted into a vector (a list of numbers representing its meaning) using
   Sentence-Transformers.
3. Your question is converted into a vector the same way.
4. FAISS finds the chunks whose vectors are mathematically closest to your question's vector
   — this is "semantic search," and it works even if you don't use the exact same words as
   the document.
5. The most relevant chunks are handed to the LLM with instructions to answer **using only
   this information** — reducing the chance of the AI inventing a policy that doesn't exist.

### Dashboard (`pages/2_Dashboard.py`)

Pure data visualization — no AI involved. It runs aggregate SQL queries directly (via
`database/queries.py`) and renders them as Plotly charts: gender/age/condition distributions,
top doctors by patient load, admissions over time, and more.

---

## Safety: How We Stop Dangerous SQL

Since an AI model writes real SQL queries, we can't just trust it blindly. Two independent
layers of protection exist:

**Layer 1 — `utils/validators.py`:** every generated SQL statement is checked before it runs.
It must:
- Start with `SELECT` (or a `WITH ... SELECT`)
- Contain no `DELETE`, `DROP`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, or similar keywords
- Contain no SQL comments or multiple chained statements

If any check fails, the query is rejected before it ever reaches the database.

**Layer 2 — the database connection itself is read-only** (`database/db.py` uses SQLite's
`mode=ro` URI option). Even in a worst-case scenario where Layer 1 somehow missed something,
the connection itself would still physically refuse to write or delete data.

---

## Testing

```bash
python tests/test_validators.py
python tests/test_database.py
```

- `test_validators.py` — confirms dangerous SQL (`DROP TABLE`, `DELETE`, chained statements,
  hidden comments) is always rejected, and safe `SELECT` statements always pass.
- `test_database.py` — confirms your CSV imports correctly and the row counts match.

---

## Troubleshooting

**"Could not reach Ollama"** — Ollama isn't running, or the model in `.env` doesn't match
what you pulled. Run `ollama list` to check, and `ollama serve` if the server itself isn't
up (though on Windows it's usually already running as a background service).

**Windows: `ollama` command not found** — this is a PATH issue, not a missing install. Either
restart your terminal after installing, or call it via its full path:
```
"C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe" list
```

**`table patients has no column named ...`** — usually means an old `data/hospital.db` from
a previous attempt still exists with an outdated schema. Delete it and re-import:
```bash
rm data/hospital.db
python -c "from database.db import import_csv_if_needed; import_csv_if_needed()"
```

**`ImportError: cannot import name 'FPDF' from 'fpdf'`** — you have both the old `fpdf`
package and `fpdf2` installed, and they conflict (both use the same module name). Fix:
```bash
pip uninstall --yes fpdf
pip install --upgrade fpdf2
```
(Keep `fpdf2` — that's the one this project actually uses. Don't uninstall it.)

---

## Future Improvements

This is intentionally a focused, beginner-friendly build. Natural next steps if you want to
extend it:
- Role-based login (Admin / Doctor / Nurse / Receptionist)
- A page to browse/search patient records directly (no AI needed)
- An audit log page showing every SQL query the AI has generated
- Switching to OpenAI instead of Ollama (already supported — just set `LLM_PROVIDER=openai`
  and `OPENAI_API_KEY` in `.env`, no code changes needed)
- Deploying to Streamlit Cloud, Render, or Railway

---

## License

This project is provided as-is for educational purposes.
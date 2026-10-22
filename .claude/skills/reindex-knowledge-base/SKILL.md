---
name: reindex-knowledge-base
description: Index or re-index the PDF knowledge base into pgvector (rag_document / rag_chunk) with script_index.py, then confirm retrieval works. Use after adding, replacing or editing a PDF in backend/docs, or when RAG answers "No se encontró información relevante."
argument-hint: [--only <file.pdf> | --reset]
---

# Re-index the knowledge base

`backend/script_index.py` reads the PDFs listed in `FILES_CONFIG`, runs
`preprocessing_service` (cleanup, quality gate, dedup, chunk enrichment with
Gemini), splits them into parent chunks of 1500 chars and child chunks of 400
chars, embeds the chunks with `gemini-embedding-001`, and writes them to
PostgreSQL. `vivienda.pdf` gets special per-project splitting
(`split_vivienda_by_project`).

## Before running

1. `backend/.env` must have `DATABASE_URL` and `GEMINI_API_KEY`/`GOOGLE_API_KEY`.
   Check that the variables are set without printing their values.
2. Find out which database `DATABASE_URL` points to. If it looks like
   production (Cloud SQL host, or the user said so), confirm with the user
   before writing to it. **`--reset` deletes all indexed documents. Always ask
   before running it.**
3. The `rag_document`/`rag_chunk` tables come from the external dashboard
   project. On a fresh database, run `backend/docs/add_rag_columns.sql` after
   creating those tables, or full-text search will find nothing.

## Run

From `backend/` with the venv active:

| Situation | Command |
|---|---|
| New PDF added to `FILES_CONFIG` | `python script_index.py` (already-indexed files are skipped) |
| One PDF changed | `python script_index.py --only <file.pdf>` |
| Chunking or preprocessing logic changed | `python script_index.py --reset` (ask first) |

Indexing calls Gemini for enrichment and embeddings, so a large PDF can take
minutes and can hit 429 rate limits. Run it in the background and read the log.

## Verify retrieval

Replace `<dept_key>` with a key from `DEPT_TO_TITLE` and ask something the PDF answers:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app.rag import search_by_department as s; print(s('<question in Spanish>', '<dept_key>'))"
```

Good output has `[Fuente: <Title>, Pág. N, Sim: 0.xx]` blocks. If it prints
"No se encontró información relevante.", check in this order:

1. `rag_document.title` matches `DEPT_TO_TITLE[<dept_key>]` exactly, accents included.
2. `rag_document.status = 'indexed'`.
3. `rag_chunk.content_tsvector` is populated (the trigger from `add_rag_columns.sql` exists).
4. `MIN_SIMILARITY` in `rag.py` (0.25) is not filtering everything out.

Report the per-file chunk counts from the indexer log and the verification output to the user.

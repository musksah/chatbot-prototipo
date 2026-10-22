# CLAUDE.md

Multi-agent customer-service chatbot for a Colombian cooperative, served over
WhatsApp (Meta Cloud API) and a React web UI. Backend is FastAPI + LangGraph +
Gemini; retrieval is hybrid search on PostgreSQL/pgvector.

**This repository is public.** Never commit secrets, phone numbers, cédulas,
generated certificates, client documents or internal URLs. Run the
`public-repo-check` skill before any commit that adds files.

## Layout

```
backend/
  app/
    main.py              FastAPI app: /chat, /chat/result, /webhook/whatsapp, /internal/*
    agent.py             LangGraph graph: State, prompts, all agents, routing
    tools.py             Transfer tools (To*), RAG tools (consultar_*), OTP + certificate tools
    rag.py               Hybrid search (vector + Spanish FTS, RRF), parent expansion, optional rerank
    preprocessing_service.py  PDF cleanup, quality gate, dedup, chunk enrichment (used by indexer)
    whatsapp.py          Webhook parsing, Graph API send, tenant handlers
    tenants.py           phone_number_id -> TenantConfig registry (multi-WABA)
    db_writer.py         asyncpg writes: whatsapp_contacts, sessions, conversations (schema v4.0)
    database.py, models/, schemas/, api/   SQLAlchemy read side for /api/conversations
    cloud_tasks.py       Enqueues /internal/process-* in production
    otp.py, pdf_generator.py, gcs_storage.py   Certificate flow (currently disabled)
    debug.py             stream_graph_with_debug (async), toggled by DEBUG_GRAPH
    explouse/bot.py      Second tenant: single-LLM bot, no LangGraph
  script_index.py        Offline indexer: docs/*.pdf -> rag_document / rag_chunk
  docs/*.sql             Migrations for RAG columns and checkpoint tables
  tests/locustfile.py    Load test (the only test in the repo)
frontend-react/          React 19 + Vite chat UI and conversations viewer
```

## Commands

Backend (run from `backend/`, venv activated):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python script_index.py                 # index PDFs not yet indexed
python script_index.py --only vivienda.pdf
python script_index.py --reset         # wipe and re-index everything
locust -f tests/locustfile.py --host=http://localhost:8000
```

Frontend (from `frontend-react/`): `npm install`, `npm run dev`, `npm run lint`, `npm run build`.

Full stack: `docker compose up` (backend on :8000, frontend on :3000).

## Environment

Backend reads `backend/.env` (there is no `.env.example` yet).

| Variable | Needed for |
|---|---|
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | Every LLM and embedding call. `explouse/bot.py` reads only `GEMINI_API_KEY`. |
| `DATABASE_URL` | RAG, checkpointer, conversation logging. Without it the graph falls back to `MemorySaver` and every RAG tool returns an error string. |
| `ENVIRONMENT=production` | Switches `/chat` and the webhook to Cloud Tasks |
| `INTERNAL_SECRET`, `CLOUD_RUN_URL`, `GOOGLE_CLOUD_PROJECT` | Cloud Tasks and `/internal/*` auth |
| `COOTRADECUN_*`, `EXPLOUSE_*` (`PHONE_NUMBER_ID`, `ACCESS_TOKEN`, `VERIFY_TOKEN`) | WhatsApp tenants. A tenant with no phone id is skipped. |
| `TWILIO_*`, `GCS_BUCKET_NAME`, `GCP_PROJECT_ID` | Certificate flow only |
| `DEBUG_GRAPH=true` | Step-by-step graph logging |

`rag_document` and `rag_chunk` are created by an external dashboard project,
not by this repo. `backend/docs/add_rag_columns.sql` only adds the hybrid-search
columns and the tsvector trigger.

## How the agent graph works

- `START -> summarize -> primary_assistant` on every turn. `route_from_start`
  always returns `primary_assistant`, so the router re-decides on each message.
- The primary assistant calls a transfer tool (`ToVivienda`, `ToNominas`, ...).
  `route_primary` maps it to `enter_<dept>`, which pushes `dialog_state` and
  hands off to the department agent.
- Each department is built by `create_workflow(name, runnable, tools, state)`:
  agent node, `<name>_tools` ToolNode, and `CompleteOrEscalate` -> `leave_skill`
  -> back to the primary assistant.
- `Assistant.__call__` retries up to 3 times when the model returns empty
  content, "stalls" (narrates instead of calling a tool, see `_STALLING_PHRASES`),
  or skips a required OTP tool call.
- Department RAG tools go through `_invoke_retriever_with_expansion`: Gemini
  query expansion (2 rewrites), one hybrid search per query, dedup, RRF sort.
- The department name is the key everywhere: `DEPT_TO_TITLE` in `rag.py` maps it
  to `rag_document.title`, which must match the title in `FILES_CONFIG` in
  `script_index.py`. Adding a department means touching all of these. Use the
  `add-department-agent` skill.
- Certificates agent is wired into the graph but disabled: `ToCertificados` is
  commented out of `primary_tools`, the router prompt and `route_primary`.

## Conventions

- Prompts and every user-facing string are Spanish. Code, docstrings and logs
  are mostly English. Keep that split.
- Replies are formatted for WhatsApp, not Markdown. Every agent prompt appends
  `WHATSAPP_FORMAT_RULE`, and `whatsapp_formatter.markdown_to_whatsapp` cleans
  up leftovers. New prompts must include the rule.
- Gemini can return `content` as a list of parts. Normalize it the way
  `handle_cootradecun` does before treating it as a string.
- Model id `gemini-3.1-flash-lite-preview` is hardcoded in `agent.py`, `rag.py`,
  `tools.py` and `explouse/bot.py`. Change all of them together.
- DB writes in `db_writer.py` swallow and log their own errors so a DB outage
  never blocks a reply. Keep new writes non-fatal the same way.
- Logs use emoji prefixes (`📥`, `🔧`, `📚`, `❌`). Match them.

## Known issues

Check whether these are still present before relying on these code paths.

- `main._run_graph` (used by `/chat` in dev and by `/internal/process-chat`)
  calls the async `stream_graph_with_debug` without `await`, and calls the sync
  `get_state` on a graph that may use `AsyncPostgresSaver`. The web UI chat path
  is broken. The WhatsApp path (`handle_cootradecun`) awaits correctly and works.
- `/chat/fake_whatsapp` reads `request.phone` and `request.name`, which
  `ChatRequest` lacks, and calls the undefined names `_detect_fallback`,
  `_extract_intent` and `_COST_PER_OUTPUT_TOKEN_USD`.
- `frontend-react/src/App.jsx` `pollResult` polls `GET /chat/fake_whatsapp`
  instead of `GET /chat/result/{taskId}`.
- `api/deps.require_any_role` allows every request, so `/api/conversations/*`
  (user phones and messages) is unauthenticated.
- `Login.jsx` checks a hardcoded password on the client, and `tools.py` hardcodes
  the OTP destination phone (`FIXED_OTP_PHONE`).
- `requirements.txt` is unpinned and still lists `langchain-openai`, which is unused.
- There are no unit tests. `TESTING_GUIDE.md` describes a plan, not existing tests.

## Verifying changes

There is no pytest suite. To check agent or routing changes, run the
`chat-smoke-test` skill. It drives the graph directly with `MemorySaver` and
prints which agent answered and which tools were called. Never test against
the WhatsApp webhook with real tenant tokens set, because it sends real messages.

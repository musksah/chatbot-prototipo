---
name: add-department-agent
description: Add a new department agent (a new knowledge domain with its own PDF, RAG tool and LangGraph sub-workflow) to the chatbot. Use when the user wants the bot to answer about a new area, e.g. "agrega un agente de seguros" or "add a department for X".
argument-hint: <dept_key> "<Document Title>" <file.pdf>
---

# Add a department agent

A department is identified by one snake_case key (e.g. `seguros`). That key and
the document title have to match exactly across five files. Missing one of them
fails silently: the router never routes there, or RAG returns
"No se encontró información relevante.".

Inputs: `dept_key`, a human title in Spanish (e.g. `Seguros`), and the PDF filename.
Ask for any of them that are missing. Also ask which topics the department
covers, because that text goes into the router rules and the agent prompt.

## Steps

1. **PDF.** Put the PDF in `backend/docs/`. Confirm with the user that it is
   publishable, since this repo is public.

2. **Indexer:** in `backend/script_index.py`, add `("<file>.pdf", "<Title>", "<dept_key>")` to `FILES_CONFIG`.

3. **RAG:** in `backend/app/rag.py`, add `"<dept_key>": "<Title>"` to `DEPT_TO_TITLE`.
   The title must equal the one in `FILES_CONFIG`.

4. **Tools:** in `backend/app/tools.py`:
   - Add a transfer model `To<Name>(BaseModel)` with a one-line English
     docstring and a `request: str` field, next to the other `To*` classes.
   - Add the RAG tool next to the other `consultar_*` tools:
     ```python
     @tool
     def consultar_<dept_key>(query: str):
         """Useful to answer questions about <topics in English>."""
         return _invoke_retriever_with_expansion("<dept_key>", query)
     ```

5. **Graph:** in `backend/app/agent.py`:
   - Import `To<Name>` and `consultar_<dept_key>` from `.tools`.
   - Add `"<dept_key>"` to the `Literal[...]` in `State.dialog_state`.
   - Write `<dept_key>_prompt` by copying an existing department prompt (e.g.
     `tesoreria_prompt`). Keep the four "REGLA CRÍTICA" lines, the escalation
     rule, `+ WHATSAPP_FORMAT_RULE +` and `Current time: {time}`. Then define
     `<dept_key>_tools = [consultar_<dept_key>, CompleteOrEscalate]` and
     `<dept_key>_runnable`.
   - Add `To<Name>` to `primary_tools`, and add a routing line
     `"- <TITLE> (<keywords>) → To<Name>\n"` to `primary_prompt`.
   - Add `"<dept_key>"` to the destinations list of the
     `add_conditional_edges("summarize", ...)` call.
   - Call `create_workflow("<dept_key>", <dept_key>_runnable, <dept_key>_tools, "<dept_key>")`.
   - In `route_primary`, add an `elif` for `To<Name>.__name__` returning
     `"enter_<dept_key>"`, and add `"enter_<dept_key>"` to that call's destinations list.
   - Add the new department to the "ESCALAR" list of the other department
     prompts whose topics overlap with it, so they hand off instead of answering.

6. **Index:** run the `reindex-knowledge-base` skill with `--only <file>.pdf`.

7. **Verify:** run the `chat-smoke-test` skill with one question for the new
   department and one follow-up that should escalate out of it. Expect
   `agent=<dept_key>` and a `consultar_<dept_key>` tool call on the first turn.

## Check before finishing

```bash
cd backend && python -c "from app.agent import builder; builder.compile(); print('graph ok')"
```

If this fails with an unknown-node error, a destinations list or `create_workflow` call is missing.

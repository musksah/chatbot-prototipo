---
name: public-repo-check
description: Scan staged changes, or the whole tracked tree, for secrets, personal data (phones, cédulas, names), client documents and internal infrastructure before committing or pushing to this public repo. Use before any commit that adds files, before pushing, or when the user asks whether the repo is safe to share.
argument-hint: [--all]
---

# Public repo check

This repo is public on GitHub. Anything committed is effectively published,
even if a later commit deletes it, because it stays in the git history.

Scope: by default, staged changes (`git diff --cached`). With `--all`, every
tracked file (`git ls-files`) plus history for the patterns in step 1.

## 1. Secrets

Search the scope for:

- Google API keys `AIza[0-9A-Za-z_-]{35}`, OpenAI `sk-`, Twilio `AC[0-9a-f]{32}` / `SK[0-9a-f]{32}`, Meta tokens `EAA[0-9A-Za-z]+`
- `-----BEGIN .*PRIVATE KEY-----`, `"type": "service_account"`
- Hardcoded passwords: `password\s*=`, `validPassword`, and literal strings compared against user input
- `postgresql://user:pass@` connection strings
- Any `.env*` file other than `.env.example`. `frontend-react/.env.production` is tracked; check that it only holds a public URL.

For `--all`, also run `git log -p --all -S '<pattern>'` for each key prefix
found, because a secret removed from HEAD is still exposed in history.

## 2. Personal data

- Colombian mobile numbers: `\+?57\s?3\d{9}` and bare `3\d{9}`
- Cédulas: 8–10 digit numbers in filenames, fixtures, logs and generated PDFs.
  `1234567890` is the known fake value and is fine.
- Files under `backend/generated_pdfs/`, `debug_output.json`, `*.log`,
  `tests/results/`, and notebook outputs in `*.ipynb`, which can contain real
  conversations
- Real names next to phone numbers or IDs

## 3. Client and internal material

- Client-identifying docs: `Docs/Propuesta*`, `Docs/Analisis_Costos*`,
  `Docs/Modelo_Datos_Costos*`, pricing images, logos
- Knowledge-base PDFs in `backend/docs/`. Ask the user whether each one is
  public information or internal to the client.
- Internal infrastructure: Cloud Run URLs (`*.run.app`), GCP project ids,
  bucket names hardcoded as defaults

## Report

List findings grouped by severity:

- **Critical:** live secrets. Tell the user to rotate them now. Removing them from the repo is not enough.
- **High:** personal data and client documents.
- **Medium:** internal URLs and ids.

Give file and line for each finding. Do not print secret values: show only the
first 4 characters.

Fixes:

- Unstage the file or move the value to an env var.
- Add generated outputs to `.gitignore`.
- For anything already pushed, explain that cleaning history needs
  `git filter-repo` plus a force push, and that forks or clones may keep a copy.
  Do not rewrite history or force-push yourself. Leave that to the user.

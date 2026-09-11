# Contributing to LitScope Local

Thanks for your interest in improving LitScope Local.

> **Development credit**: This project was developed with assistance from **Xiaomi MIMO — MiMo-X-Pro-Preview**.  
> Substantial portions of the initial application (backend adapters, query bridge, native deploy path, frontend Claude DESIGN tokens, and docs) were produced in an assisted engineering workflow with that model. Please keep this notice when forking or substantially rewriting the README.

[中文 README](./README.md) · [English README](./README.en.md)

---

## Ways to contribute

- Bug reports and reproducible issues  
- Docs fixes (typos, clearer setup steps, OS-specific notes)  
- Source adapter improvements (rate-limit handling, field mapping)  
- UI/UX polish that stays within the existing design tokens  
- Tests (parser, dedup, export, adapter contract tests)  

Please **do not** open PRs that:

- Add Google Scholar scraping or other ToS-violating collectors  
- Introduce multi-tenant auth without a prior design discussion  
- Bundle large binary assets or secrets (`.env`, API keys)  

---

## Before you start

1. Read the [English README](./README.en.md) or [中文 README](./README.md) and get the app running natively.  
2. Search existing [Issues](https://github.com/IDKURLOVE/literature-search-local/issues) to avoid duplicates.  
3. For larger changes, open an issue first to discuss scope.  

---

## Dev environment

```bash
git clone https://github.com/IDKURLOVE/literature-search-local.git
cd literature-search-local

# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
pytest -q

# Frontend (other terminal)
cd ../frontend
npm install
npm run dev
```

Default stack for contributors: **SQLite + in-process scheduler**. You do not need Docker.

Useful env for local work (`.env` in repo root or export in shell):

```env
CROSSREF_MAILTO=you@example.com
ENABLE_SCHEDULER=true
REFRESH_MODE=inline
```

---

## Project map (where to change what)

| Area | Path |
|---|---|
| WOS parser | `backend/app/search.py` |
| Query → source free text / years | `backend/app/query_bridge.py` |
| Source adapters | `backend/app/sources/*.py` |
| Shared polite HTTP client | `backend/app/sources/http_util.py` |
| Dedup / synthetic IDs | `backend/app/sources/__init__.py` |
| API routes | `backend/app/routers/` |
| Topic refresh (Celery + inline) | `backend/app/tasks.py` |
| In-process scheduler | `backend/app/main.py` |
| Design tokens (Claude DESIGN.md) | `frontend/src/styles/tokens.css` |
| Ant Design theme | `frontend/src/App.tsx` |
| Pages | `frontend/src/pages/` |
| Native start script | `scripts/start-local.ps1` |

Visual tokens must stay aligned with **Claude DESIGN.md** (`#faf9f5` canvas, `#cc785c` primary, serif display). Do not invent a second brand palette.

---

## Coding guidelines

### Backend (Python)

- Python 3.11+, type hints on public functions  
- SQLAlchemy 2.0 async style; load relationships with `selectinload` when accessed under async  
- Prefer small pure functions for parsing/dedup so they stay unit-testable  
- Academic HTTP calls go through `app.sources.http_util` (User-Agent + clearer 429 errors)  
- Do not commit `backend/litscope.db`  

### Frontend (TypeScript / React)

- Strict TypeScript; no `any` in new code without a comment explaining why  
- Reuse existing components (`SearchBox`, `PaperCard`, `TopicList`, …)  
- User-facing copy in Chinese by default (match the existing UI); keep labels short and action-oriented  
- Respect `prefers-reduced-motion` and focus-visible states  

### Commits

- Prefer concise, imperative subjects in English (repo history is English)  
  - Good: `fix: reconstruct OpenAlex abstract from inverted index`  
  - Avoid: `update` / `fix stuff`  
- Reference issue numbers when applicable (`#12`)  
- Do not mix unrelated refactors with a single bugfix PR  

---

## Tests you should run

```bash
# Backend unit tests
cd backend && pytest -q

# Frontend typecheck + build
cd frontend && npm run build

# Optional live smoke (network + rate limits)
cd .. && python scripts/live_search_smoke.py
```

PRs that change search/export/dedup **must** include or update unit tests under `backend/tests/`.

---

## Pull request process

1. Fork and create a branch from `master`  
   - `feat/...`, `fix/...`, `docs/...`  
2. Implement with tests; keep the diff focused  
3. Run the test commands above and paste results in the PR description  
4. Fill the PR template fields (problem, approach, verification)  
5. Be ready to iterate on review comments  

Maintainers may squash-merge small PRs.

---

## Reporting bugs

Include:

- OS and versions (`python -V`, `node -v`)  
- Exact steps to reproduce  
- Expected vs actual  
- Relevant logs (backend console, browser network tab)  
- Whether you used native SQLite or Docker/Postgres  

Security-sensitive findings: do not post secrets; open a private report if possible, or scrub credentials before posting.

---

## Design / product notes

- Single-user local tool: prioritize clarity over enterprise features  
- Rate limits are environmental; prefer graceful per-source errors over hard failures  
- Keep Xiaomi MIMO attribution in README headers when making doc-wide rewrites  

---

## License

By contributing, you agree that your contributions are licensed under the MIT License of this repository.

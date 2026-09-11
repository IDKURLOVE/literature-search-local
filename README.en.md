# LitScope Local

Local literature aggregation search and research-topic manager: run Web-of-Science-style queries across open academic APIs, save queries as research topics with automatic refresh, then favorite papers, tag them, write notes, and export citations.

> **Attribution**: This project was developed with **Xiaomi MIMO — MiMo-X-Pro-Preview**.

**Default deployment is native (SQLite + in-process scheduler). Docker, PostgreSQL, and Redis are not required.**

| | |
|---|---|
| Backend | Python 3.11+ / FastAPI / SQLAlchemy 2 |
| Frontend | Node.js 18+ / React 18 / Vite / Ant Design 5 |
| Storage | SQLite by default (PostgreSQL optional) |
| Sources | Crossref · OpenAlex · Semantic Scholar · PubMed · arXiv |
| Users | Single-user, no login (localhost / private network only) |

中文文档：[README.md](./README.md)

---

## Table of contents

1. [Quick start for newcomers](#1-quick-start-for-newcomers)
2. [Requirements](#2-requirements)
3. [Install and run (recommended)](#3-install-and-run-recommended)
4. [Manual step-by-step setup](#4-manual-step-by-step-setup)
5. [Environment variables](#5-environment-variables)
6. [How to use the product](#6-how-to-use-the-product)
7. [Query syntax cheat sheet](#7-query-syntax-cheat-sheet)
8. [API examples](#8-api-examples)
9. [Optional: Docker Compose](#9-optional-docker-compose)
10. [Optional: PostgreSQL](#10-optional-postgresql)
11. [Tests and smoke checks](#11-tests-and-smoke-checks)
12. [Project layout](#12-project-layout)
13. [FAQ / troubleshooting](#13-faq--troubleshooting)
14. [Security and limitations](#14-security-and-limitations)
15. [Contributing](#15-contributing)
16. [License](#16-license)

---

## 1. Quick start for newcomers

Six steps (same idea on Windows / macOS / Linux):

1. **Install tooling**: Python 3.11+, Node.js 18+, Git  
2. **Clone the repo**
3. **Copy config**: `.env.example` → `.env` (set `CROSSREF_MAILTO` at minimum)
4. **Install deps**: backend `pip install -r requirements.txt`, frontend `npm install`
5. **Start**: uvicorn + vite (or the Windows one-shot script)
6. **Open** <http://localhost:3000>, type a sample query, click **Search**

Health check:

```bash
curl http://127.0.0.1:8000/api/health
# expect e.g. {"status":"ok","database":"sqlite",...}
```

---

## 2. Requirements

| Component | Version | Check |
|---|---|---|
| Python | 3.11+ | `python -V` |
| Node.js | 18+ | `node -v` |
| npm | ships with Node | `npm -v` |
| Git | any recent | `git -v` |

Optional:

- **Docker + Compose** only if you want containers  
- **PostgreSQL 14+** only if you do not want SQLite  
- Outbound HTTPS access to academic APIs  

> On Windows, if `python` is missing, try `py -V`.  
> Corporate networks may cause timeouts or HTTP 429 — see [FAQ](#13-faq--troubleshooting).

---

## 3. Install and run (recommended)

### 3.1 Clone

```bash
git clone https://github.com/IDKURLOVE/literature-search-local.git
cd literature-search-local
```

### 3.2 Configure

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS / Linux**

```bash
cp .env.example .env
nano .env
```

**Change at least this line** (use your real email; Crossref recommends a mailto to reduce rate limits):

```env
CROSSREF_MAILTO=you@example.com
```

Everything else can stay default (SQLite + topic refresh every 6 hours in-process).

### 3.3 One-shot start on Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1
```

The script creates a backend venv, installs deps, starts API on 8000, and starts the frontend on 3000.

### 3.4 Start on macOS / Linux

```bash
# Terminal A: backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///$(pwd)/litscope.db"
export ENABLE_SCHEDULER=true
export REFRESH_MODE=inline
export CROSSREF_MAILTO="you@example.com"
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal B: frontend
cd frontend
npm install
npm run dev
```

### 3.5 Open the UI

| URL | Purpose |
|---|---|
| <http://localhost:3000> | App (search / topics / library) |
| <http://127.0.0.1:8000/docs> | Swagger API docs |
| <http://127.0.0.1:8000/api/health> | Health check |

---

## 4. Manual step-by-step setup

### 4.1 Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pytest -q          # optional: expect 15 passed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

First boot creates `backend/litscope.db` and tables automatically.

### 4.2 Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server defaults to <http://localhost:3000> and proxies `/api` to `http://localhost:8000` (see `frontend/vite.config.ts`).

### 4.3 Production frontend build (optional)

```bash
cd frontend
npm run build
# output: frontend/dist — serve statically and reverse-proxy /api to :8000
```

---

## 5. Environment variables

See [`.env.example`](.env.example) for the full template.

| Variable | Default | Required | Notes |
|---|---|---|---|
| `DATABASE_URL` | SQLite file under `backend/` | No | Database URL |
| `ENABLE_SCHEDULER` | `true` | No | In-process topic refresh |
| `SCHEDULER_INTERVAL_HOURS` | `6` | No | Refresh interval (hours, min 1) |
| `REFRESH_MODE` | `auto` | No | `inline` = never Celery; `auto` = try Celery then fallback |
| `CROSSREF_MAILTO` | empty | **Strongly recommended** | Polite pool email for Crossref/OpenAlex |
| `SEMANTIC_SCHOLAR_API_KEY` | empty | No | Avoids harsh 429s on S2 |
| `CORS_ORIGINS` | `http://localhost:3000,...` | No | Comma-separated allowed origins |

Docker/Celery-only vars (ignore for native mode): `POSTGRES_*`, `REDIS_PORT`, `CELERY_*`, `TOPIC_REFRESH_CRONTAB`, `BACKEND_PORT`, `FRONTEND_PORT`.

---

## 6. How to use the product

### 6.1 Search

1. Open the home page  
2. Enter a query, for example:

   ```text
   TI="large language model" AND PY=2023-2024
   ```

3. Select sources (at least one; defaults are Crossref + OpenAlex)  
4. Click **Search**  
5. Use **DOI / Source / PDF** links; click **Save** to store into the local library  

### 6.2 Research topics

- Click **Save as research topic** on the result divider to persist the current query  
- On the **Topics** page, refresh or delete topics manually  
- With `ENABLE_SCHEDULER=true`, all topics refresh on the configured interval  

### 6.3 Library

- Favorited papers and topic-refreshed papers appear under **Library**  
- Edit **tags** and **notes**, then **Save tags & notes**  
- Multi-select → choose BibTeX / RIS / Plain Text → **Export**  

---

## 7. Query syntax cheat sheet

| Tag | Field | Example |
|---|---|---|
| `TI=` | Title | `TI=transformer` |
| `AU=` | Author | `AU=lecun` |
| `AB=` | Abstract | `AB=representation` |
| `SO=` | Source / journal | `SO=nature` |
| `PY=` | Year or range | `PY=2023` or `PY=2020-2024` |
| `DO=` | DOI | `DO=10.1038/xxx` |
| `TS=` | Topic | `TS=graph neural network` |
| `AF=` | All fields | `AF=bert` |
| `IS=` | ISSN | `IS=0028-0836` |

Operators:

- `AND` / `OR` / `NOT`
- Parentheses: `(AU=lecun OR AU=bengio) AND PY=2018-2024`
- Phrases: `TI="attention is all you need"`
- Proximity: `TI=graph NEAR/3 neural` (terms are collected; deep proximity filtering is simplified)

Notes:

- No space between the field tag and `=` (`TI=` OK, `TI =` bad)  
- Crossref/OpenAlex handle Chinese queries poorly — prefer English keywords  

---

## 8. API examples

Base URL: `http://127.0.0.1:8000`

### Health

```bash
curl http://127.0.0.1:8000/api/health
```

### Aggregate search

```bash
curl -X POST http://127.0.0.1:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TI=\"machine learning\" AND PY=2020-2024",
    "sources": ["crossref", "openalex"],
    "limit": 5
  }'
```

`sources` reports per-source `ok/error`. `query_translation` shows extracted years and free text.

### Create a topic

```bash
curl -X POST http://127.0.0.1:8000/api/topics/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LLM 2023",
    "query": "TI=\"large language model\" AND PY=2023",
    "sources": ["crossref", "openalex"]
  }'
```

### Refresh a topic

```bash
curl -X POST http://127.0.0.1:8000/api/topics/<topic_id>/refresh
```

### Library list / update tags & notes

```bash
curl http://127.0.0.1:8000/api/papers/

curl -X PUT http://127.0.0.1:8000/api/papers/<paper_id> \
  -H "Content-Type: application/json" \
  -d '{"tags":["survey","llm"],"notes":"Read section 3 carefully"}'
```

### Export BibTeX

```bash
curl -X POST http://127.0.0.1:8000/api/export/ \
  -H "Content-Type: application/json" \
  -d '{"paper_ids":["<paper_id>"],"format":"bibtex"}'
```

---

## 9. Optional: Docker Compose

**Only if Docker is already installed.** Prefer section 3 otherwise.

```bash
cp .env.example .env
# set CROSSREF_MAILTO
docker compose up -d --build
```

| Service | Host port (default) | Role |
|---|---|---|
| frontend | 3000 → container 80 | nginx static + `/api` proxy |
| backend | 8000 | FastAPI |
| worker | — | Celery worker + beat |
| db | 5432 | Postgres 16 (pgvector image) |
| redis | 6379 | broker/cache |

```bash
docker compose logs -f backend
docker compose down
```

> Compose files are kept as an optional path. The current maintainer environment does not run Docker; prefer native mode if anything fails.

---

## 10. Optional: PostgreSQL

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/litscope
ENABLE_SCHEDULER=true
REFRESH_MODE=inline
```

`asyncpg` is already in `requirements.txt`. Tables are created on first boot via `create_all`.

---

## 11. Tests and smoke checks

```bash
# backend unit tests
cd backend
pip install -r requirements.txt
pytest -q
# expect: 15 passed

# frontend typecheck + build
cd ../frontend
npm install
npm run build

# live academic API smoke (network required; may 429)
cd ..
python scripts/live_search_smoke.py
python scripts/probe_apis.py
```

```bash
curl http://127.0.0.1:8000/api/health
```

---

## 12. Project layout

```text
literature-search-local/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI + in-process scheduler
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py          # Topic / Paper
│   │   ├── schemas.py
│   │   ├── search.py          # WOS parser
│   │   ├── query_bridge.py
│   │   ├── tasks.py           # refresh (Celery or inline)
│   │   ├── routers/
│   │   └── sources/           # five adapters + polite HTTP client
│   ├── tests/
│   └── requirements.txt
├── frontend/src/
├── scripts/start-local.ps1
├── docs/compose/spec/
├── docker-compose.yml         # optional
├── CONTRIBUTING.md
├── .env.example
├── README.md                  # Chinese
└── README.en.md               # English (this file)
```

---

## 13. FAQ / troubleshooting

### UI loads but search fails

1. Is the API up? `curl http://127.0.0.1:8000/api/health`  
2. Is the Vite proxy pointing at 8000? (`frontend/vite.config.ts`)  
3. CORS errors in the browser console → align `CORS_ORIGINS`  

### Empty search results

- Fix syntax (`TI=` with no space)  
- Confirm outbound API access  
- Set `CROSSREF_MAILTO`  
- Try a single source (e.g. Crossref only)  

### Many `429 Too Many Requests`

OpenAlex / arXiv / Semantic Scholar rate-limit shared IPs hard.

- Slow down  
- Set `CROSSREF_MAILTO`  
- Set `SEMANTIC_SCHOLAR_API_KEY`  
- Retry later; one failing source does not fail the whole search  

### `uvicorn` / `python` not found

- Windows: `py -3.11` or full path; activate the venv  
- macOS/Linux: `python3`; `source .venv/bin/activate`  

### Ports in use

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

uvicorn app.main:app --port 8001
```

Also update Vite proxy / CORS if you change ports.

### Topic stays at `last_results_count=0`

- Query too narrow?  
- Click **Refresh** and read backend logs  
- Rate limits can temporarily yield zero hits  

### Where is the SQLite file?

`backend/litscope.db` (gitignored). Back it up by copying the file.

### Reset everything

Stop servers → delete `backend/litscope.db` → start again (schema recreates).

### Docker issues

This project does **not** require Docker. Use section 3 if you have no Docker.

---

## 14. Security and limitations

- **Single-user, no auth**. Default bind is local. **Do not expose to the public internet.**  
- Follow each academic API’s terms; configure a real `mailto`.  
- No Google Scholar scraping.  
- No PDF full-text manager, no multi-user ACL.  
- Chinese databases (e.g. CNKI) are not integrated.  

---

## 15. Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md).

**Development credit**: LitScope Local was initially developed with **Xiaomi MIMO — MiMo-X-Pro-Preview**. Subsequent contributions are welcome via issues and pull requests.

---

## 16. License

MIT

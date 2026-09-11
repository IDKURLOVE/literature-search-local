# LitScope Local

**English** · [中文](./README.md)

Local literature aggregation search and topic tracking: query multiple open academic sources with Web of Science–style syntax, save searches as research topics with scheduled refresh, then favorite papers, tag them, write notes, and export citations.

> **Credit**: Built with assistance from **Xiaomi MIMO — MiMo-X-Pro-Preview**.

**Default deploy mode: native (SQLite + in-process scheduler). No Docker, Postgres, or Redis required.**

| | |
|---|---|
| Backend | Python 3.11+ / FastAPI / SQLAlchemy 2 |
| Frontend | Node.js 18+ / React 18 / Vite / Ant Design 5 |
| Data | SQLite by default (PostgreSQL optional) |
| Sources | Crossref · OpenAlex · Semantic Scholar · PubMed · arXiv |
| Users | Single-user, no login — local / LAN only |

---

## Contents

1. [Quick start for newcomers](#1-quick-start-for-newcomers)
2. [Requirements](#2-requirements)
3. [Install & run (recommended)](#3-install--run-recommended)
4. [Manual step-by-step](#4-manual-step-by-step)
5. [Environment variables](#5-environment-variables)
6. [How to use the app](#6-how-to-use-the-app)
7. [Query syntax cheat sheet](#7-query-syntax-cheat-sheet)
8. [API examples](#8-api-examples)
9. [Optional: Docker Compose](#9-optional-docker-compose)
10. [Optional: PostgreSQL](#10-optional-postgresql)
11. [Tests & self-check](#11-tests--self-check)
12. [Project layout](#12-project-layout)
13. [FAQ / troubleshooting](#13-faq--troubleshooting)
14. [Security & limitations](#14-security--limitations)
15. [Contributing](#15-contributing)
16. [License](#16-license)

---

## 1. Quick start for newcomers

Six steps (Windows / macOS / Linux):

1. **Install** Python 3.11+, Node.js 18+, Git  
2. **Clone** this repository  
3. **Copy config**: `.env.example` → `.env` (set `CROSSREF_MAILTO` at minimum)  
4. **Install deps**: backend `pip install -r requirements.txt`, frontend `npm install`  
5. **Start**: backend uvicorn + frontend vite (or the Windows one-shot script)  
6. **Open** <http://localhost:3000>, enter an example query, click **Search**

Health check:

```bash
curl http://127.0.0.1:8000/api/health
# expect: {"status":"ok","database":"sqlite",...}
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

- **Docker + Compose** — only for the container path  
- **PostgreSQL 14+** — only if you skip SQLite  
- Outbound internet access to academic APIs  

---

## 3. Install & run (recommended)

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

**Minimum change** (use your real email — Crossref recommends a `mailto` to reduce rate limits):

```env
CROSSREF_MAILTO=you@example.com
```

Defaults: SQLite + in-process refresh every 6 hours.

### 3.3 Windows one-shot

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1
```

This creates the backend venv, installs deps, starts API on **8000** and frontend on **3000**.

### 3.4 macOS / Linux

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

### 3.5 URLs

| URL | Purpose |
|---|---|
| <http://localhost:3000> | UI (Search / Topics / Library) |
| <http://127.0.0.1:8000/docs> | Swagger |
| <http://127.0.0.1:8000/api/health> | Health |

---

## 4. Manual step-by-step

### 4.1 Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

First start creates `backend/litscope.db` and tables automatically.

### 4.2 Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server defaults to <http://localhost:3000> and proxies `/api` → `http://localhost:8000`.

### 4.3 Production frontend build (optional)

```bash
cd frontend
npm run build
# output: frontend/dist — serve statically and reverse-proxy /api to :8000
```

---

## 5. Environment variables

See [`.env.example`](.env.example).

| Variable | Default | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | SQLite file path | No | DB URL |
| `ENABLE_SCHEDULER` | `true` | No | In-process topic refresh |
| `SCHEDULER_INTERVAL_HOURS` | `6` | No | Refresh interval (min 1) |
| `REFRESH_MODE` | `auto` | No | `inline` = never Celery; `auto` = Celery with inline fallback |
| `CROSSREF_MAILTO` | empty | **Strongly recommended** | Polite-pool email for Crossref/OpenAlex |
| `SEMANTIC_SCHOLAR_API_KEY` | empty | No | Optional S2 key (avoids many 429s) |
| `CORS_ORIGINS` | `http://localhost:3000,...` | No | Comma-separated allowed origins |

Docker/Celery-only vars (ignore for native mode): `POSTGRES_*`, `REDIS_PORT`, `CELERY_*`, `TOPIC_REFRESH_CRONTAB`, `BACKEND_PORT`, `FRONTEND_PORT`.

---

## 6. How to use the app

### 6.1 Search

1. On the home page, enter a query, e.g.

   ```text
   TI="large language model" AND PY=2023-2024
   ```

2. Select sources (at least one; default Crossref + OpenAlex)  
3. Click **Search**  
4. Open **DOI / Source / PDF** from each card; click **Save** to store into the library  

### 6.2 Research topics

- Click **Save as research topic** under the result count to persist the current query  
- On **Topics**, refresh or delete manually  
- With `ENABLE_SCHEDULER=true`, the process refreshes all topics on an interval  

### 6.3 Library

- Favorited papers and topic-refresh papers appear under **Library**  
- Edit **tags** and **notes**, then **Save tags & notes**  
- Select papers → choose BibTeX / RIS / Plain Text → **Export**  

---

## 7. Query syntax cheat sheet

| Tag | Meaning | Example |
|---|---|---|
| `TI=` | Title | `TI=transformer` |
| `AU=` | Author | `AU=lecun` |
| `AB=` | Abstract | `AB=representation` |
| `SO=` | Source / venue | `SO=nature` |
| `PY=` | Year or range | `PY=2023` or `PY=2020-2024` |
| `DO=` | DOI | `DO=10.1038/xxx` |
| `TS=` | Topic | `TS=graph neural network` |
| `AF=` | All fields | `AF=bert` |
| `IS=` | ISSN | `IS=0028-0836` |

Operators:

- `AND` / `OR` / `NOT`
- Parentheses: `(AU=lecun OR AU=bengio) AND PY=2018-2024`
- Phrases in double quotes: `TI="attention is all you need"`
- Proximity: `TI=graph NEAR/3 neural` (terms are collected; deep proximity filtering is simplified)

Notes:

- No space between the field tag and `=` (`TI=` OK, `TI =` not OK)  
- Chinese queries work poorly on Crossref/OpenAlex; prefer English keywords  

---

## 8. API examples

Base URL: `http://127.0.0.1:8000`

### Health

```bash
curl http://127.0.0.1:8000/api/health
```

### Aggregated search

```bash
curl -X POST http://127.0.0.1:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TI=\"machine learning\" AND PY=2020-2024",
    "sources": ["crossref", "openalex"],
    "limit": 5
  }'
```

`sources` reports `ok`/`error` per provider; `query_translation` shows parsed years and free text.

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

### Library & notes

```bash
curl http://127.0.0.1:8000/api/papers/

curl -X PUT http://127.0.0.1:8000/api/papers/<paper_id> \
  -H "Content-Type: application/json" \
  -d '{"tags":["survey","llm"],"notes":"Deep-read section 3"}'
```

### Export BibTeX

```bash
curl -X POST http://127.0.0.1:8000/api/export/ \
  -H "Content-Type: application/json" \
  -d '{"paper_ids":["<paper_id>"],"format":"bibtex"}'
```

---

## 9. Optional: Docker Compose

**Only if Docker Engine/Desktop + Compose is already installed.** Native mode (section 3) is preferred.

```bash
cp .env.example .env
# set CROSSREF_MAILTO
docker compose up -d --build
```

| Service | Host port (default) | Role |
|---|---|---|
| frontend | 3000 → 80 | nginx static + `/api` proxy |
| backend | 8000 | FastAPI |
| worker | — | Celery worker + beat |
| db | 5432 | Postgres 16 (pgvector image) |
| redis | 6379 | broker/cache |

---

## 10. Optional: PostgreSQL

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/litscope
ENABLE_SCHEDULER=true
REFRESH_MODE=inline
```

`asyncpg` is already in `requirements.txt`. Tables are created on first start.

---

## 11. Tests & self-check

```bash
cd backend
pip install -r requirements.txt
pytest -q
# expect: 15 passed

cd ../frontend
npm install
npm run build

cd ..
python scripts/live_search_smoke.py
python scripts/probe_apis.py
```

---

## 12. Project layout

```text
literature-search-local/
├── backend/app/          # FastAPI, WOS parser, adapters, routers
├── frontend/src/         # React UI + Claude DESIGN tokens
├── scripts/              # start-local.ps1 + smoke tests
├── docs/compose/spec/    # feature spec
├── docker-compose.yml    # optional
├── .env.example
├── README.md             # Chinese
├── README.en.md          # English (this file)
└── CONTRIBUTING.md
```

---

## 13. FAQ / troubleshooting

### UI loads, search fails

1. Is API up? `curl http://127.0.0.1:8000/api/health`  
2. Check Vite proxy in `frontend/vite.config.ts`  
3. Check `CORS_ORIGINS` for browser CORS errors  

### Empty results

- Fix query syntax (no space after `TI=`)  
- Confirm outbound network  
- Set `CROSSREF_MAILTO`  
- Try a single source (e.g. Crossref only)  

### HTTP 429 rate limits

OpenAlex / arXiv / Semantic Scholar throttle shared IPs.

- Slow down; set mailto / S2 API key  
- Per-source failures appear under `sources` without failing the whole search  

### `uvicorn` / `python` not found

- Windows: try `py -3.11` or activate the venv  
- Unix: use `python3` and `source .venv/bin/activate`  

### Port already in use

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000
uvicorn app.main:app --port 8001
```

### Where is the SQLite file?

`backend/litscope.db` (gitignored). Copy the file to back up.

### Start clean

Stop servers → delete `backend/litscope.db` → start again.

---

## 14. Security & limitations

- Single-user, no auth — bind to localhost; **do not expose to the public internet**  
- Respect each academic API’s terms; configure a real `mailto`  
- No Google Scholar scraping  
- No multi-user auth, no full-text PDF management  
- No CNKI / Chinese proprietary databases  

---

## 15. Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

**This project was developed with Xiaomi MIMO — MiMo-X-Pro-Preview.** When opening issues or PRs, please mention that context if your change builds on MIMO-generated scaffolding.

---

## 16. License

MIT

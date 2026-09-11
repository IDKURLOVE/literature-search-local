# Contributing to LitScope Local

Thanks for your interest in improving LitScope Local.

> **Development attribution**  
> The initial implementation of this repository was developed with **Xiaomi MIMO — MiMo-X-Pro-Preview** (Xiaomi’s MiMo coding agent).  
> Please keep this credit in the README, release notes, and derivative documentation when you redistribute or substantially fork the project.

中文贡献说明见文末摘要；英文流程为准。

---

## Ways to contribute

- Report bugs (GitHub Issues)
- Improve docs (README zh/en, comments, examples)
- Fix adapters / rate-limit handling
- Add tests
- Implement features from the roadmap below (open an issue first for large items)

**Out of scope (please do not PR):**

- Google Scholar scrapers
- Multi-tenant auth systems (unless discussed)
- Breaking the single-user local-first defaults without an issue thread

---

## Development setup

Prerequisites: Python 3.11+, Node.js 18+, Git.

```bash
git clone https://github.com/IDKURLOVE/literature-search-local.git
cd literature-search-local
cp .env.example .env
# set CROSSREF_MAILTO=you@example.com

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q

# Frontend (another terminal)
cd ../frontend
npm install
npm run build
```

Run locally:

```bash
# backend
cd backend && source .venv/bin/activate
export DATABASE_URL="sqlite+aiosqlite:///$(pwd)/litscope.db"
export REFRESH_MODE=inline
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm run dev
```

Windows one-shot: `scripts\start-local.ps1`

---

## Ground rules

1. **Evidence over invention** — do not invent API endpoints, field names, or third-party behaviors. Cite docs or code when claiming how something works.
2. **Keep the local-first defaults** — SQLite + in-process scheduler must keep working without Docker/Redis.
3. **Polite HTTP** — all outbound academic API calls should go through `backend/app/sources/http_util.py` (User-Agent + mailto + clear 429 errors).
4. **No secrets in git** — never commit `.env`, API keys, or `litscope.db`.
5. **UI language** — default user-facing copy is Chinese; keep labels consistent. English docs live in `README.en.md`.
6. **Design tokens** — frontend visuals follow Claude DESIGN.md tokens in `frontend/src/styles/tokens.css`. Do not introduce a second brand palette.

---

## Pull request process

1. Open an issue for non-trivial changes (skip for typos / tiny fixes).
2. Fork and create a branch: `git checkout -b feat/short-name`
3. Make focused commits. Suggested prefixes:
   - `feat:` new capability
   - `fix:` bug fix
   - `docs:` documentation only
   - `test:` tests only
   - `refactor:` no behavior change
4. **Before you push**, run:

   ```bash
   cd backend && pytest -q          # expect 15+ passed
   cd ../frontend && npm run build  # tsc + vite must pass
   ```

5. Update docs when behavior changes (`README.md`, `README.en.md`, `.env.example`).
6. Open a PR with:
   - What / why
   - How you verified (commands + results)
   - Screenshots for UI changes
7. Keep PRs small when possible; large dumps are hard to review.

### Commit message example

```text
fix: rebuild OpenAlex abstracts from inverted index

OpenAlex never returns a plain abstract field. Reconstruct text from
abstract_inverted_index so library cards show abstracts.
```

---

## Adding a new data source

1. Create `backend/app/sources/<name>.py` with:

   ```python
   async def search(request: SearchRequest, translated: TranslatedQuery) -> list[PaperCreate]: ...
   ```

2. Register it in `SOURCE_MAP` in `backend/app/sources/__init__.py`.
3. Use `http_util.get_json` / `get_text` only.
4. Map fields into `PaperCreate` (title required; prefer DOI).
5. Add unit tests for mapping/dedup if logic is non-trivial.
6. Document the source in both READMEs.

---

## Testing checklist

- [ ] `pytest -q` green in `backend/`
- [ ] `npm run build` green in `frontend/`
- [ ] Manual smoke: `/api/health`, one search, create topic, export sample
- [ ] No new dependency without justification in the PR body

Live API calls may return `429` — that is environmental. Prefer mocked unit tests for CI-sensitive logic.

---

## Reporting bugs

Include:

- OS and versions (`python -V`, `node -v`)
- Exact steps to reproduce
- Expected vs actual
- Relevant logs (backend console, browser network tab)
- Whether native or Docker mode

Security issues: do not file a public issue with exploit details; contact the maintainer privately when possible.

---

## License

By contributing, you agree that your contributions are licensed under the MIT License of this repository.

---

## 中文摘要

- 本仓库初始版本由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助开发；请在 README / 衍生文档中保留该署名。
- 贡献前请跑通：`backend/pytest -q` 与 `frontend/npm run build`。
- 保持「本地优先」：无 Docker 时 SQLite + 进程内调度必须可用。
- 外网请求必须走 `http_util`，禁止提交 `.env` / 密钥 / 数据库文件。
- 新数据源：实现 `search(request, translated)` 并注册到 `SOURCE_MAP`。
- PR 请说明验证命令与结果；大改动先开 Issue。

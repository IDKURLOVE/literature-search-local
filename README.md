# LitScope Local

本地文献聚合检索与主题管理 Web 应用（**默认无需 Docker**）。

> **开发标注**：本项目由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助搭建完成。

## 功能

- 类 WOS 高级检索语法（`TI=` `AU=` `PY=` `AND/OR/NOT` `NEAR/x`）
- 多源聚合：Crossref / OpenAlex / Semantic Scholar / PubMed / arXiv
- 结果去重（DOI 优先，标题+首作者+年份指纹兜底）
- 研究主题保存 + 定时刷新（进程内调度；可选 Celery）
- 收藏 / 标签 / 笔记 / BibTeX·RIS·Plain 导出
- 单用户免登录

## 推荐：原生部署（无 Docker）

依赖：Python 3.11+、Node.js 18+。默认使用 **SQLite** + **进程内定时刷新**。

### Windows 一键

```powershell
cd literature-search-local
Copy-Item .env.example .env
# 编辑 .env，填写 CROSSREF_MAILTO
powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1
```

- UI：<http://localhost:3000>
- API：<http://127.0.0.1:8000/api/health>
- 文档：<http://127.0.0.1:8000/docs>

### 手动分步

```bash
# 后端
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 默认 DATABASE_URL=sqlite+aiosqlite:///./litscope.db
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

### 环境变量（`.env`）

| 变量 | 默认 | 说明 |
|---|---|---|
| `DATABASE_URL` | SQLite 文件 | 可改为 Postgres |
| `ENABLE_SCHEDULER` | `true` | 进程内定时刷新主题 |
| `SCHEDULER_INTERVAL_HOURS` | `6` | 刷新间隔 |
| `REFRESH_MODE` | `auto` | `inline` 强制进程内；`auto` 可回退 Celery |
| `CROSSREF_MAILTO` | 空 | 强烈建议填写，降低限流 |

## 可选：Docker Compose

若你已有 Docker，仍可：

```bash
cp .env.example .env
docker compose up -d --build
```

> 当前维护环境已移除 Docker Desktop；Compose 文件保留为可选路径。

## 测试

```bash
cd backend && python -m pytest -q
cd frontend && npm run build
python scripts/live_search_smoke.py   # 真实 API 冒烟（可能遇 429 限流）
```

## 设计系统

前端视觉 token 来自 [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 的 **Claude DESIGN.md**（暖纸色画布 + 珊瑚主色 + 衬线标题），实现于 `frontend/src/styles/tokens.css` 与 Ant Design `ConfigProvider`。

## 目录

```
literature-search-local/
├── backend/                 # FastAPI + 五源适配器 + 可选 Celery
├── frontend/                # React + Vite + Ant Design
├── scripts/start-local.ps1  # 原生一键启动
├── docs/compose/spec/
├── docker-compose.yml       # 可选
└── .env.example
```

## License

MIT

# LitScope Local

本地文献聚合检索与主题管理 Web 应用：用类 Web of Science 语法，一次查多个开放学术源，把检索式存成「研究主题」并自动刷新，再收藏、打标签、写笔记、导出引用。

> **开发标注**：本项目由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助搭建完成。

**默认部署方式：原生运行（SQLite + 进程内调度），不需要 Docker、Postgres、Redis。**

| | |
|---|---|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2 |
| 前端 | Node.js 18+ / React 18 / Vite / Ant Design 5 |
| 数据 | 默认 SQLite（可切 PostgreSQL） |
| 数据源 | Crossref · OpenAlex · Semantic Scholar · PubMed · arXiv |
| 用户模型 | 单用户免登录，仅建议本机/内网使用 |

---

## 目录

1. [别人怎么从零跑起来](#1-别人怎么从零跑起来)
2. [系统要求](#2-系统要求)
3. [安装与启动（推荐）](#3-安装与启动推荐)
4. [手动分步安装](#4-手动分步安装)
5. [环境变量说明](#5-环境变量说明)
6. [产品怎么用](#6-产品怎么用)
7. [检索语法速查](#7-检索语法速查)
8. [API 示例](#8-api-示例)
9. [可选：Docker Compose](#9-可选docker-compose)
10. [可选：接 PostgreSQL](#10-可选接-postgresql)
11. [测试与自检](#11-测试与自检)
12. [目录结构](#12-目录结构)
13. [常见问题（FAQ / 排错）](#13-常见问题faq--排错)
14. [安全与限制](#14-安全与限制)
15. [License](#15-license)

---

## 1. 别人怎么从零跑起来

按顺序做这 6 步即可（Windows / macOS / Linux 通用思路）：

1. **装环境**：Python 3.11+、Node.js 18+、Git  
2. **克隆仓库**
3. **复制并修改配置**：`.env.example` → `.env`（至少填 `CROSSREF_MAILTO`）
4. **装依赖**：后端 `pip install -r requirements.txt`，前端 `npm install`
5. **启动**：后端 uvicorn + 前端 vite（或 Windows 一键脚本）
6. **打开** <http://localhost:3000>，在搜索框输入示例查询并点「搜索」

验证后端是否活着：

```bash
curl http://127.0.0.1:8000/api/health
# 期望类似：{"status":"ok","database":"sqlite",...}
```

---

## 2. 系统要求

| 组件 | 版本 | 检查命令 |
|---|---|---|
| Python | 3.11 或更高 | `python -V` |
| Node.js | 18 或更高 | `node -v` |
| npm | 随 Node 安装 | `npm -v` |
| Git | 任意近期版本 | `git -v` |

可选：

- **Docker + Compose**：仅当你想用容器部署时需要  
- **PostgreSQL 14+**：仅当你不想用 SQLite 时需要  
- 能访问外网（学术 API）

> Windows 若 `python` 不可用，可试 `py -V`。  
> 若公司网络限制，学术源可能超时或 429，见 [FAQ](#13-常见问题faq--排错)。

---

## 3. 安装与启动（推荐）

### 3.1 克隆

```bash
git clone https://github.com/IDKURLOVE/literature-search-local.git
cd literature-search-local
```

### 3.2 配置

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS / Linux**

```bash
cp .env.example .env
nano .env   # 或 vim .env
```

**最少改这一行**（用你的真实邮箱，Crossref 官方建议带 mailto，可降低限流）：

```env
CROSSREF_MAILTO=you@example.com
```

其余可保持默认（SQLite + 进程内每 6 小时刷新主题）。

### 3.3 Windows 一键启动

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1
```

脚本会自动：创建后端虚拟环境 → 安装依赖 → 启动 API(8000) → 启动前端(3000)。

### 3.4 macOS / Linux 启动

```bash
# 终端 A：后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///$(pwd)/litscope.db"
export ENABLE_SCHEDULER=true
export REFRESH_MODE=inline
export CROSSREF_MAILTO="you@example.com"
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 B：前端
cd frontend
npm install
npm run dev
```

### 3.5 打开界面

| 地址 | 用途 |
|---|---|
| <http://localhost:3000> | 主界面（检索 / 研究主题 / 文献库） |
| <http://127.0.0.1:8000/docs> | Swagger API 文档 |
| <http://127.0.0.1:8000/api/health> | 健康检查 |

---

## 4. 手动分步安装

若不用一键脚本，按下面逐步执行。

### 4.1 后端

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pytest -q          # 可选：确认 15 个单测通过
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

首次启动会在 `backend/` 下自动创建 `litscope.db` 并建表。

### 4.2 前端

```bash
cd frontend
npm install
npm run dev
```

开发模式默认 <http://localhost:3000>，`/api` 会代理到 `http://localhost:8000`（见 `frontend/vite.config.ts`）。

### 4.3 生产构建前端（可选）

```bash
cd frontend
npm run build
# 产物在 frontend/dist，可用任意静态服务器托管，并把 /api 反代到 8000
```

---

## 5. 环境变量说明

完整模板见 [`.env.example`](.env.example)。

| 变量 | 默认 | 必填 | 说明 |
|---|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///.../backend/litscope.db` | 否 | 数据库连接串 |
| `ENABLE_SCHEDULER` | `true` | 否 | 是否启用进程内定时刷新研究主题 |
| `SCHEDULER_INTERVAL_HOURS` | `6` | 否 | 定时刷新间隔（小时，最小 1） |
| `REFRESH_MODE` | `auto` | 否 | `inline`=只用进程内；`auto`=优先 Celery，失败回退进程内 |
| `CROSSREF_MAILTO` | 空 | **强烈建议** | Crossref/OpenAlex 礼貌池邮箱 |
| `SEMANTIC_SCHOLAR_API_KEY` | 空 | 否 | Semantic Scholar Key（无 Key 易 429） |
| `CORS_ORIGINS` | `http://localhost:3000,...` | 否 | 逗号分隔的前端源 |

Docker/Celery 专用（原生模式可忽略）：`POSTGRES_*`、`REDIS_PORT`、`CELERY_*`、`TOPIC_REFRESH_CRONTAB`、`BACKEND_PORT`、`FRONTEND_PORT`。

---

## 6. 产品怎么用

### 6.1 检索

1. 打开首页「检索开放学术源」  
2. 输入查询，例如：

   ```text
   TI="large language model" AND PY=2023-2024
   ```

3. 勾选数据源（至少一个；默认 Crossref + OpenAlex）  
4. 点「搜索」  
5. 结果卡片可点 **DOI / 来源 / PDF**；点 **收藏** 写入本地文献库  

### 6.2 保存研究主题

- 在结果分隔条上点 **「保存为检索主题」** → 把当前检索式存成主题  
- 打开 **研究主题** 页，可手动 **刷新** 或删除  
- 若 `ENABLE_SCHEDULER=true`，进程会按间隔自动刷新全部主题  

### 6.3 文献库

- **收藏** 过的文献、主题刷新入库的文献都会出现在 **文献库**  
- 可编辑 **标签** 与 **笔记**，点「保存标签与笔记」  
- 勾选多篇 → 选格式（BibTeX / RIS / Plain Text）→ **导出** 下载  

---

## 7. 检索语法速查

| 字段标签 | 含义 | 示例 |
|---|---|---|
| `TI=` | 标题 | `TI=transformer` |
| `AU=` | 作者 | `AU=lecun` |
| `AB=` | 摘要 | `AB=representation` |
| `SO=` | 期刊/来源 | `SO=nature` |
| `PY=` | 年份或区间 | `PY=2023` 或 `PY=2020-2024` |
| `DO=` | DOI | `DO=10.1038/xxx` |
| `TS=` | 主题 | `TS=graph neural network` |
| `AF=` | 全部字段 | `AF=bert` |
| `IS=` | ISSN | `IS=0028-0836` |

算符：

- `AND` / `OR` / `NOT`
- 括号组合：`(AU=lecun OR AU=bengio) AND PY=2018-2024`
- 短语用双引号：`TI="attention is all you need"`
- 邻近：`TI=graph NEAR/3 neural`（当前实现会收集词项，深度邻近过滤为简化版）

注意：

- 字段标签与 `=` 之间**不要有空格**（`TI=` 正确，`TI =` 错误）  
- 中文检索在 Crossref/OpenAlex 上效果有限，优先英文关键词  

---

## 8. API 示例

Base URL：`http://127.0.0.1:8000`

### 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

### 聚合搜索

```bash
curl -X POST http://127.0.0.1:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TI=\"machine learning\" AND PY=2020-2024",
    "sources": ["crossref", "openalex"],
    "limit": 5
  }'
```

响应中的 `sources` 会标明每个源 `ok/error`；`query_translation` 显示解析出的年份与自由文本。

### 创建研究主题

```bash
curl -X POST http://127.0.0.1:8000/api/topics/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LLM 2023",
    "query": "TI=\"large language model\" AND PY=2023",
    "sources": ["crossref", "openalex"]
  }'
```

### 手动刷新主题

```bash
curl -X POST http://127.0.0.1:8000/api/topics/<topic_id>/refresh
```

### 列出文献库 / 更新标签笔记

```bash
curl http://127.0.0.1:8000/api/papers/

curl -X PUT http://127.0.0.1:8000/api/papers/<paper_id> \
  -H "Content-Type: application/json" \
  -d '{"tags":["survey","llm"],"notes":"精读第 3 节"}'
```

### 导出 BibTeX

```bash
curl -X POST http://127.0.0.1:8000/api/export/ \
  -H "Content-Type: application/json" \
  -d '{"paper_ids":["<paper_id>"],"format":"bibtex"}'
```

---

## 9. 可选：Docker Compose

**仅当你已安装 Docker Desktop / Docker Engine + Compose 插件。**  
推荐路径仍是第 3 节原生部署。

```bash
cp .env.example .env
# 编辑 .env，填写 CROSSREF_MAILTO
docker compose up -d --build
```

服务：

| 服务 | 端口（默认） | 说明 |
|---|---|---|
| frontend | 3000 → 容器 80 | nginx 静态 + `/api` 反代 |
| backend | 8000 | FastAPI |
| worker | — | Celery worker + beat |
| db | 5432 | Postgres 16 (pgvector 镜像) |
| redis | 6379 | 队列/缓存 |

```bash
docker compose logs -f backend
docker compose down
```

> 说明：开发环境曾验证过 Compose 文件结构，但当前维护机未再跑通 Docker 运行时；若你遇到问题优先用原生模式。

---

## 10. 可选：接 PostgreSQL

已有 Postgres 时，在 `.env` 中设置：

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/litscope
ENABLE_SCHEDULER=true
REFRESH_MODE=inline
```

并安装对应驱动（`requirements.txt` 已含 `asyncpg`）。首次启动会自动 `create_all` 建表。

---

## 11. 测试与自检

```bash
# 后端单元测试（解析器 / 去重 / 导出 / OpenAlex 摘要重建）
cd backend
pip install -r requirements.txt
pytest -q
# 期望：15 passed

# 前端类型检查 + 构建
cd ../frontend
npm install
npm run build

# 真实学术 API 冒烟（依赖外网，可能 429）
cd ..
python scripts/live_search_smoke.py
python scripts/probe_apis.py
```

接口自检（服务已启动时）：

```bash
curl http://127.0.0.1:8000/api/health
```

---

## 12. 目录结构

```text
literature-search-local/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口 + 进程内调度
│   │   ├── config.py          # 环境变量
│   │   ├── database.py        # async engine
│   │   ├── models.py          # Topic / Paper
│   │   ├── schemas.py         # Pydantic 契约
│   │   ├── search.py          # WOS 语法解析器
│   │   ├── query_bridge.py    # AST → 年份/自由文本
│   │   ├── tasks.py           # 主题刷新（Celery/inline）
│   │   ├── routers/           # search/topics/papers/export
│   │   └── sources/           # 五源适配器 + HTTP 礼貌客户端
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/             # 检索 / 主题 / 文献库
│       ├── components/
│       ├── styles/tokens.css  # Claude DESIGN tokens
│       └── api/client.ts
├── scripts/
│   ├── start-local.ps1        # Windows 一键
│   ├── live_search_smoke.py
│   └── probe_apis.py
├── docs/compose/spec/
├── docker-compose.yml         # 可选
├── .env.example
└── README.md
```

---

## 13. 常见问题（FAQ / 排错）

### 启动后前端能开，搜索失败

1. 后端是否在 8000：`curl http://127.0.0.1:8000/api/health`  
2. 前端代理是否指向后端：开发模式看 `frontend/vite.config.ts` 的 `server.proxy`  
3. 浏览器控制台是否 CORS 错误：确认 `.env` 的 `CORS_ORIGINS` 含前端源  

### 搜索结果为空

- 检查查询语法（`TI=` 后不要空格）  
- 确认外网可访问学术 API  
- 填写 `CROSSREF_MAILTO`  
- 换数据源再试（例如只勾 Crossref）  

### 大量 `429 Too Many Requests`

OpenAlex / arXiv / Semantic Scholar 对公共 IP 限流较严。

- 降低并发与频率  
- 填写 `CROSSREF_MAILTO`  
- 申请并配置 `SEMANTIC_SCHOLAR_API_KEY`  
- 稍后再试；单源失败不会拖垮其它源（响应 `sources` 里会标 `error`）  

### `uvicorn` / `python` 不是命令

- Windows：用 `py -3.11` 或完整路径；或先激活 venv  
- macOS/Linux：用 `python3`；确认 `source .venv/bin/activate`  

### 端口被占用

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 改端口
uvicorn app.main:app --port 8001
# 前端 vite.config.ts 里改 server.port，并同步 CORS / proxy
```

### 主题一直 `last_results_count=0`

- 主题里的 query 是否过窄  
- 手动点「刷新」并看后端日志  
- 确认 `ENABLE_SCHEDULER=true` 或手动能触发 inline 刷新  
- 学术源限流时可能暂时 0 结果  

### SQLite 文件在哪

默认：`backend/litscope.db`（已 gitignore）。备份直接拷贝该文件即可。

### 想清空重来

停掉前后端 → 删除 `backend/litscope.db` → 再启动（会自动重建表）。

### Docker 相关

- 本项目**不强制 Docker**  
- Compose 路径需要你本机已有 Docker；若没有请用第 3 节原生方式  

---

## 14. 安全与限制

- **单用户免登录**，默认监听 `127.0.0.1` / 本机端口，**不要直接暴露公网**  
- 学术 API 使用请遵守各源服务条款；请配置真实 `mailto`  
- 不做 Google Scholar 爬取  
- 不做 PDF 全文下载管理、多用户权限  
- 中文文献源（如知网）未接入  

---

## 15. License

MIT

---

**署名**：LitScope Local 由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助开发完成。  
Issues / PR 欢迎提交到本仓库。

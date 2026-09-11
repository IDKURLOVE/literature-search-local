---
feature: litscope-local
status: delivered
updated: 2026-09-11
branch: master
commits: pending
---

# LitScope Local 文献检索应用

## Report

**What was built** — 完整可部署的本地文献聚合检索应用 LitScope Local：FastAPI 后端（五源适配器、WOS 查询桥、去重、主题/文献/导出路由、Celery 定时刷新），React 前端（检索 / 研究主题 / 文献库，Claude DESIGN token），以及 Docker Compose 一键编排。项目由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助开发，并已在 README、健康检查与页脚标注。

**Verification** — `backend: pytest` **15 passed**；`frontend: npm run build`（`tsc --noEmit && vite build`）**PASS**。本机无 Docker，`compose up` 未做运行时验证。

**Journey log**
1. 实施指南存在会直接跑挂的代码（ExportRequest 缺失、BibTeX f-string、PaperOut 用于瞬时搜索结果），实现时按契约修复而非照抄。
2. WOS tokenizer 中 `\S+` 会吞掉 `)`，括号查询失败；改为 `[^\s()"]+`。
3. OpenAlex 摘要须从 `abstract_inverted_index` 重建。
4. async SQLAlchemy 懒加载 `topic.papers` 会 `MissingGreenlet`；Celery 任务改用 `selectinload`。
5. 搜索「收藏」原先误建 Topic；改为 `POST /api/papers/` 真正入库。

## [S1] Problem

研究者需要在本地一键部署的 Web 应用中，用类 WOS 语法聚合检索 Crossref / OpenAlex / Semantic Scholar / PubMed / arXiv，保存研究主题并定时刷新，对文献收藏、打标签、写笔记、导出引用。

## [S2] Design

### 架构

- FastAPI + SQLAlchemy 2 async + PostgreSQL(+pgvector 镜像) + Redis + Celery worker/beat
- React 18 + Vite + TypeScript + Ant Design 5 + TanStack Query + Zustand
- Docker Compose：db / redis / backend / worker / frontend(nginx)

### 关键契约（相对实施指南的修复）

1. **搜索响应**：`SearchResult.papers` 使用 `PaperSearchHit`（含 `id: UUID`，未入库时为 `uuid5(NAMESPACE_URL, doi or title+year)`），不再错误要求完整 `PaperOut` DB 行。
2. **WOS 查询接线**：`WOSQueryParser` 解析 AST 后由 `app/query_bridge.py` 转为：
   - `filters.from_year` / `until_year`（来自 `PY=`）
   - 各源可接受的自由文本 / 字段提示
3. **导出**：补全 `ExportRequest` schema；修复 BibTeX author join 的 f-string。
4. **去重**：`first_author` 比较统一为姓氏小写；DB 层用 DOI 优先。
5. **Celery crontab**：解析 `TOPIC_REFRESH_CRONTAB` 为 celery `crontab(minute, hour, day_of_month, month_of_year, day_of_week)`，默认 `0 */6 * * *`。

### 视觉（awesome-design-md → claude）

以 `E:\awesome-design-md\design-md\claude\DESIGN.md` 为唯一 token 真相：

| token | hex |
|---|---|
| canvas | `#faf9f5` |
| surface-soft | `#f5f0e8` |
| ink | `#141413` |
| body | `#3d3d3a` |
| muted | `#6c6a64` |
| hairline | `#e6dfd8` |
| primary | `#cc785c` |
| primary-active | `#a9583e` |
| success | `#5db872` |
| error | `#c64545` |

- 展示标题：`Georgia, 'Times New Roman', serif`（Copernicus 回退）
- 正文：`Inter, 'Segoe UI', system-ui`
- 代码/DOI：`JetBrains Mono, ui-monospace, monospace`
- 圆角 6–12px；主按钮 40px；禁止第二品牌 accent

### API

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| POST | `/api/search/` | 聚合搜索 |
| CRUD | `/api/topics/` | 研究主题 |
| POST | `/api/topics/{id}/refresh` | 手动刷新 |
| POST | `/api/papers/` | 收藏入库（按 DOI upsert） |
| CRUD | `/api/papers/{id}` | 文献标签/笔记 |
| POST | `/api/export/` | BibTeX/RIS/Plain |

## [S3] Out of Scope

- Google Scholar 爬虫、多用户登录、PDF 全文下载管理、LLM 综述、云端/K8s 部署

## Tasks

- [x] T1: 后端核心（config/database/models/schemas/search/query_bridge） — acceptance: 模块可 import，解析器单测通过 (covers: S2)
- [x] T2: 五源适配器 + 去重 + search_all — acceptance: 假响应可聚合去重；异常源标记 error (covers: S2)
- [x] T3: 路由 + Celery 任务 — acceptance: FastAPI 可挂载；ExportRequest 完整 (covers: S2)
- [x] T4: 后端单测 — acceptance: pytest 全绿 (covers: S2)
- [x] T5: 前端 DESIGN token + 页面/组件 — acceptance: tsc + vite build 通过 (covers: S2)
- [x] T6: Docker/Compose/.env/README（含 Xiaomi MIMO 标注） — acceptance: 文件齐全可部署 (covers: S1; S2)
- [ ] T7: 推送 GitHub 公开仓库 literature-search-local — acceptance: main/master 可见且含署名 (covers: S1)

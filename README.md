# LitScope Local

本地一键部署的文献聚合检索与主题管理 Web 应用。

> **开发标注**：本项目由 **Xiaomi MIMO — MiMo-X-Pro-Preview** 协助搭建完成。

## 功能

- 类 WOS 高级检索语法（`TI=` `AU=` `PY=` `AND/OR/NOT` `NEAR/x`）
- 多源聚合：Crossref / OpenAlex / Semantic Scholar / PubMed / arXiv
- 结果去重（DOI 优先，标题+首作者+年份指纹兜底）
- 研究主题保存 + Celery 定时刷新
- 收藏 / 标签 / 笔记 / BibTeX·RIS·Plain 导出
- 单用户免登录，Docker Compose 一键部署

## 快速开始

```bash
git clone https://github.com/IDKURLOVE/literature-search-local.git
cd literature-search-local
cp .env.example .env
# 编辑 .env，至少填写 CROSSREF_MAILTO
docker compose up -d --build
```

浏览器打开：<http://localhost:3000>

API 文档：<http://localhost:8000/docs>  
健康检查：<http://localhost:8000/api/health>

## 本地开发

### 后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 设计系统

前端视觉 token 来自 [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 的 **Claude DESIGN.md**（暖纸色画布 + 珊瑚主色 + 衬线标题），实现于 `frontend/src/styles/tokens.css` 与 Ant Design `ConfigProvider`。

## 目录

```
literature-search-local/
├── backend/          # FastAPI + Celery + 五源适配器
├── frontend/         # React + Vite + Ant Design
├── docs/compose/spec/
├── docker-compose.yml
└── .env.example
```

## License

MIT

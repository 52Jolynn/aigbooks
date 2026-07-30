# AIGBooks

匿名 AI 生成书黑名单网站。FastAPI + PostgreSQL + Vue 3 单服务器部署。

## 快速开始

```bash
# 后端
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# 前端
cd ../frontend
pnpm install
pnpm dev
```

## 文档

- 产品设计：`docs/plans/2026-07-29-aigbooks-design.md`
- 实施计划：`docs/plans/2026-07-30-aigbooks-implementation-v2.md`
- 部署指南：`deploy/README.md`

## 架构

- 后端：FastAPI + SQLAlchemy 2.0 async + PostgreSQL 15 + Alembic
- 前端：Vue 3 + Vite + TypeScript + Naive UI + Fontsource 自托管
- 存储：本地磁盘（covers + evidence）
- 部署：systemd + nginx

## License

待定。

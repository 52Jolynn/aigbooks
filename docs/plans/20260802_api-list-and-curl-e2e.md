---
创建时间: 2026-08-02 00:00
状态: 已完成
---

# 20260802-API 接口清单与 curl E2E 测试

## 概述

本文档列出 AIGBooks 后端 **所有对外接口**（业务 + 静态 + FastAPI 自动生成），并提供
对应的 curl 调用方式，作为 `scripts/e2e.sh` 测试脚本的参考依据。

- 后端版本：`AIGBooks API v0.1.0`
- 自动 OpenAPI：`GET /openapi.json`（Schema 实时反映代码注释）
- 自动文档 UI：`GET /docs`（Swagger UI）、`GET /redoc`（ReDoc）

## 1. 接口清单

### 1.1 业务接口（`/api/*`）

| 方法 | 路径 | 鉴权 | 请求 | 响应 | 路由定义 |
|------|------|------|------|------|---------|
| GET | `/api/books/recent` | 无 | — | `RecentReportsOut{reports,total}` | `app/routers/books.py:18` |
| GET | `/api/books/{isbn}` | 无 | path: `isbn` (10–17) | `BookDetailOut` / 404 | `app/routers/books.py:45` |
| POST | `/api/reports` | 无（限流 5/h/IP+FP） | `multipart/form-data`：isbn,title,author,description,fingerprint[,cover,evidences…] | 201 `ReportOut` / 422 / 429 | `app/routers/reports.py:35` |
| POST | `/api/reports/{report_id}/vote` | 无 | `application/json`：`{vote_type: ±1, fingerprint}` | 200 `ReportOut` / 404 / 422 | `app/routers/reports.py:110` |
| GET | `/api/search` | 无 | query: `q` | `SearchResultOut{reports,total,query}` | `app/routers/search.py:15` |
| GET | `/api/feed/reports.rss` | 无 | — | `application/rss+xml` | `app/routers/feed.py:28` |

### 1.2 静态资源（`/covers/*` 与 `/evidence/*`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/covers/{rel_path}` | 封面文件；`AIGBOOKS_COVERS_DIR` 根目录下的相对路径，POST `/api/reports` 时若上传 `cover`，DB `books.cover_path` 即存相对路径 |
| GET | `/evidence/{rel_path}` | 证据文件；目录布局 `YYYY/MM/<uuid><ext>`，DB `evidences.file_path` 即为相对路径 |

### 1.3 FastAPI 自动生成

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/openapi.json` | OpenAPI 3.1 Schema（`curl /openapi.json \| jq .` 可枚举所有接口） |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |

## 2. 关键约束（影响 E2E 期望值）

| 项 | 值 | 来源 |
|----|----|------|
| ISBN 长度 | 10–17 | `app/routers/reports.py:38` |
| Title 长度 | 1–500 | `app/routers/reports.py:39` |
| Author 长度 | 1–200 | `app/routers/reports.py:40` |
| Description 长度 | 1–5000 | `app/routers/reports.py:41` |
| Fingerprint 长度 | 8–128 | `app/routers/reports.py:42`、`schemas.VoteCreate` |
| `vote_type` | 字面量 `1` 或 `-1` | `schemas.VoteCreate` |
| 限流 | 5 次 / (ip+fingerprint) / 3600s | `app/config.py:33-34` + `app/middleware/rate_limit.py` |
| 单文件大小 | ≤ 20 MiB | `app/config.py:28` |
| 封面 MIME 白名单 | jpeg/png/webp | `app/services/storage.py:21-24` |
| 证据 MIME 白名单 | jpeg/png/webp/mp4 | `app/config.py:30` |

## 3. curl E2E 用例（已被 `scripts/e2e.sh` 采纳）

下面 12 个用例覆盖：

1. `GET /api/books/recent` 空库 → 200 `{reports:[],total:0}`
2. `POST /api/reports` 新 ISBN → 201
3. `POST /api/reports` 同 ISBN 聚合 → `book.report_count == 2`
4. `GET /api/books/{isbn}` 已存在 → 200 含 reports
5. `GET /api/books/{isbn}` 不存在 → 404
6. `POST /api/reports` 缺字段 → 422
7. `GET /api/search?q=中文` → 至少 2 命中
8. `GET /api/search?q=` 空字符串 → 走 ILIKE/LIKE 回退（不报错）
9. `POST /api/reports/{id}/vote` → 200 upvote=1
10. `POST /api/reports/{id}/vote` 反向 → upvote=0 downvote=1
11. `POST /api/reports/{not_exist}/vote` → 404
12. `GET /api/feed/reports.rss` → 200 且 `content-type: application/rss+xml`

外加：

13. `GET /openapi.json` → 200 包含所有 path
14. `GET /covers/{path}` 上传封面后 → 200（依赖 `cover` 上传）

## 4. 失败语义（来自 `app/middleware/exception.py`）

| 异常类 | HTTP | Body |
|--------|------|------|
| `HTTPException(404)` | 404 | `{code:404, msg:"…"}` |
| `HTTPException(415)` | 415 | `{code:415, msg:"格式不支持: …"}` |
| `HTTPException(413)` | 413 | `{code:413, msg:"文件过大"}` |
| `HTTPException(422)` | 422 | `{code:422, msg:"举报过于频繁…"}` |
| `RequestValidationError` | 422 | `{code:422, msg:"请求参数错误", errors:[…]}` |
| `SQLAlchemyError` | 500 | `{code:500, msg:"数据库错误"}` |
| `Exception`（兜底） | 500 | `{code:500, msg:"服务器内部错误"}` |

## 5. 默认数据库：SQLite

`AIGBOOKS_DATABASE_URL` 默认值已从 PostgreSQL 切换为 SQLite：

```
sqlite+aiosqlite:///./var/aigbooks.db
```

意味着：
- **新装环境零依赖即可启动**：克隆 → `uv sync` → `uv run alembic upgrade head` → `uv run uvicorn app.main:app`。
- 切换其他方言：在 `.env` 覆盖 `AIGBOOKS_DATABASE_URL`（见 `backend/.env.example`）。
- 测试套件默认即使用 SQLite 内存库（`tests/conftest.py:_sqlite_url`）。
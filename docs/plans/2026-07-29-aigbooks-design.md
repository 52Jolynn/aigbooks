# AIGBooks 产品设计文档

---
创建时间: 2026-07-29 17:20
状态: 已完成（待实施）
---

## 0. 一句话定位

**AIGBooks** = 一个**只读匿名 + 自由举报**的"AI 生成书黑名单"网站，让读书爱好者在购书前快速识别并避开 AI 生成的劣质书籍。

无账号体系、不留存任何举报人身份、零审核。

---

## 1. 产品形态与用户流程

### 1.1 读者（默认匿名访客）

1. 首页看到**最新 20 条**举报卡片（书名、作者、ISBN、举报次数、封面、举报时间）
2. 顶部搜索框：书名 / 作者 / ISBN **或**举报描述全文（PG FTS 模糊匹配）
3. 点开某书：聚合该 ISBN 的全部举报 + 总举报次数 + 每条证据（图片/视频/文字）+ 点赞/点踩

### 1.2 举报人（同一匿名入口）

1. 点首页"举报"按钮，弹出表单
2. 必填：**ISBN、书名、作者、举报描述**
3. 可选：**封面图**（默认占位图）、**证据**（文字/图片/拍照/视频，任意组合，可多份）
4. 表单支持 **Tesseract.js 客户端 OCR**：扫 ISBN 条形码 / 书脊照片 → 自动回填三项
5. 提交即生效，无审核；触发限流时返回 429

### 1.3 MVP 不做（YAGNI）

- ❌ 登录 / 注册 / 昵称
- ❌ 举报人工审核
- ❌ 举报端防滥用限流（仅 IP+指纹限流，不做语义审核）
- ❌ 外部 API 自动补全封面/简介
- ❌ 推荐榜单 / 可信作者榜单
- ❌ 评论 / 回复
- ❌ 举报内容去重（仅按 ISBN 自动聚合）

---

## 2. 架构与技术栈

### 2.1 部署拓扑（单服务器）

```
[浏览器]
   │  Vue 3 SPA + Tesseract.js（OCR 客户端运行）
   ▼
[Nginx 80/443] ── 反代 ──▶ [FastAPI :8000 (uvicorn)]
                                │
                                ├─▶ [PostgreSQL 15+]   本机 5432
                                └─▶ [/var/lib/aigbooks/evidence]   本地磁盘
```

### 2.2 技术栈选型

| 层 | 选型 | 备注 |
|---|---|---|
| 前端框架 | Vue 3 + Vite + TypeScript | 组合式 API + 类型友好 |
| 前端路由/状态 | Vue Router + Pinia | 官方推荐 |
| 前端 UI | Naive UI | 轻量、TS 原生 |
| 前端 OCR | Tesseract.js | 客户端运行，零成本 |
| 后端框架 | FastAPI | 异步高性能、自动 OpenAPI |
| ORM | SQLAlchemy 2.0 (async) + asyncpg | 现代异步栈 |
| 迁移 | Alembic | 数据库版本管理 |
| 数据库 | PostgreSQL 15+ | 内置 FTS（simple 字典） |
| 包管理 | uv | 替代 pip/venv，速度快、lock 文件 |
| 文件存储 | 本地磁盘 | 后续可换 OSS |
| 部署 | systemd + nginx + certbot | 单机最小可行 |

### 2.3 关键 API

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET`  | `/api/books/recent` | 最新 20 条举报 |
| `GET`  | `/api/search?q=` | 书名/作者/ISBN + 描述全文检索 |
| `GET`  | `/api/books/{isbn}` | 单书详情 + 全举报聚合 |
| `POST` | `/api/reports` | 提交举报（含 multipart 文件） |
| `POST` | `/api/reports/{id}/vote` | 点赞/点踩（IP + 指纹） |
| `GET`  | `/api/feed/reports.rss` | RSS 2.0 订阅最新 20 条举报 |

### 2.4 PostgreSQL FTS 设计

- `books.title` + `books.author` → 触发器同步至 `books.tsv_meta`（带 weight）
- `reports.description` → 同步至 `reports.tsv_desc`
- 搜索时用 `to_tsquery('simple', $1)` 命中两个 tsvector 并 `union`
- 中文分词先用 PG 内置 `simple` 字典（按字符切）；后续按需升级 `zhparser`

### 2.5 RSS 订阅设计

- **端点**：`GET /api/feed/reports.rss`，`Content-Type: application/rss+xml; charset=utf-8`
- **条数**：最新 20 条（与首页一致）
- **排序**：`reports.created_at DESC`
- **关联**：每条 item 链接到该书详情页 `/books/{isbn}`，并附原举报描述作 `<description>`
- **库**：`feedgen`（mature、零模板依赖，输出 RSS 2.0 / Atom 双格式）
- **缓存**：MVP 不缓存，每次请求实时生成；后续可加 `Cache-Control: max-age=300`
- **Nginx**：`location = /api/feed/reports.rss { add_header Content-Type "application/rss+xml; charset=utf-8"; }` 兜底 MIME

**item 字段映射：**

| RSS 字段 | 数据源 |
|---|---|
| `<title>` | `[{isbn}] {title} — {author}` |
| `<link>` | `https://{host}/books/{isbn}` |
| `<guid>` | `report-{id}`（保证全局唯一） |
| `<pubDate>` | `reports.created_at`（RFC822） |
| `<description>` | `reports.description`（CDATA 包裹防转义） |

---

## 3. 数据模型

```sql
-- 书籍（按 ISBN 唯一，自动聚合根）
CREATE TABLE books (
    id           BIGSERIAL PRIMARY KEY,
    isbn         TEXT NOT NULL UNIQUE,           -- 必填，去重键
    title        TEXT NOT NULL,
    author       TEXT NOT NULL,
    cover_path   TEXT,                            -- 默认 NULL，前端兜底图
    report_count INT NOT NULL DEFAULT 0,
    tsv_meta     TSVECTOR,                        -- title(A) + author(B) 加权
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX books_tsv_meta_idx ON books USING GIN(tsv_meta);

-- 举报（每条独立展示，关联 books；含 IP+指纹用于限流）
CREATE TABLE reports (
    id           BIGSERIAL PRIMARY KEY,
    book_id      BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    description  TEXT NOT NULL,                    -- 举报描述，搜索源
    tsv_desc     TSVECTOR,                         -- 描述全文检索
    upvote       INT NOT NULL DEFAULT 0,
    downvote     INT NOT NULL DEFAULT 0,
    ip           INET NOT NULL,                    -- 限流 + 审计（不展示）
    fingerprint  TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX reports_tsv_desc_idx    ON reports USING GIN(tsv_desc);
CREATE INDEX reports_book_id_idx     ON reports(book_id);
CREATE INDEX reports_rate_limit_idx  ON reports (ip, fingerprint, created_at);

-- 证据文件（每条举报可挂多份）
CREATE TABLE evidences (
    id          BIGSERIAL PRIMARY KEY,
    report_id   BIGINT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,                     -- 本地相对路径
    file_kind   TEXT NOT NULL,                     -- 'image' | 'video' | 'photo' | 'text'
    mime_type   TEXT,
    size_bytes  BIGINT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX evidences_report_id_idx ON evidences(report_id);

-- 投票（IP + 浏览器指纹复合唯一）
CREATE TABLE votes (
    id           BIGSERIAL PRIMARY KEY,
    report_id    BIGINT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    ip           INET NOT NULL,
    fingerprint  TEXT NOT NULL,
    vote_type    SMALLINT NOT NULL,                -- +1 / -1
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (report_id, ip, fingerprint)
);
```

### 3.1 关键约束

- **匿名**：四张表都不存任何昵称、邮箱、user_id
- **投票唯一**：`(report_id, ip, fingerprint)` 复合唯一 → 同一访客对同一举报仅一票，再次投票覆盖
- **聚合计数**：`books.report_count` 由 reports INSERT/DELETE 触发器维护
- **检索**：两张 tsvector 列由 AFTER INSERT/UPDATE 触发器维护
- **限流**：直接查 `reports` 表，`WHERE ip=? AND fingerprint=? AND created_at >= now() - interval '1 hour'` → 若 `count >= 5` 则拒绝

### 3.2 文件存储路径

- 封面：`/var/lib/aigbooks/covers/{isbn}.jpg`
- 证据：`/var/lib/aigbooks/evidence/{yyyy}/{mm}/{uuid}.{ext}`

### 3.3 限流逻辑

```python
async def rate_limit_report(db, ip, fp):
    cutoff = now() - timedelta(hours=1)
    count = await db.scalar(
        select(func.count()).select_from(reports)
        .where(reports.c.ip == ip,
               reports.c.fingerprint == fp,
               reports.c.created_at >= cutoff)
    )
    if count >= 5:
        raise HTTPException(429, "举报过于频繁，请稍后再试")
```

阈值：**每 (IP + 指纹) 每小时最多 5 条举报**。

---

## 4. 错误处理、测试与部署

### 4.1 错误处理

| 场景 | 处理 |
|---|---|
| ISBN 重复提交 | `INSERT ... ON CONFLICT (isbn) DO NOTHING` → 自动聚合复用 books |
| OCR 失败 / 识别错误 | 前端捕获回退手填，不阻塞提交 |
| 文件超限（单文件 20MB） | 后端校验返回 413 |
| 文件类型非法（仅 jpg/png/webp/mp4） | 后端 MIME 校验返回 415 |
| 限流触发 | 返回 429，UI 弹"请稍后再试" |
| 搜索空结果 | 前端展示"暂无相关举报" |
| 后端异常 | 全局中间件统一 JSON `{code, msg}`，避免堆栈泄漏 |

### 4.2 测试策略

- **后端**：pytest + httpx AsyncClient
  - 关键用例：举报聚合、限流（连发 6 条第 6 条 429）、搜索命中 tsvector、投票唯一约束、文件上传校验
- **前端**：Vitest + Vue Test Utils
  - 关键用例：表单校验、OCR 回填、搜索防抖、投票状态切换
- **E2E**：`scripts/e2e.sh` curl 脚本跑通"举报 → 聚合 → 搜索 → 投票"全链路

### 4.3 部署清单（单服务器）

```bash
# 1. 系统依赖
apt install postgresql-15 nginx

# 2. Python 环境（uv 管理）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync                                    # 读取 pyproject.toml + uv.lock
uv run alembic upgrade head                # 迁移
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 文件目录
mkdir -p /var/lib/aigbooks/{covers,evidence}
chown www-data:www-data /var/lib/aigbooks

# 4. systemd 服务
systemctl enable --now aigbooks-api    # uvicorn :8000
systemctl reload nginx                  # 反代 + 静态资源

# 5. HTTPS
certbot --nginx -d aigbooks.example.com
```

### 4.4 `pyproject.toml`（uv）

```toml
[project]
name = "aigbooks"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.9",
    "feedgen>=1.0",
]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "httpx>=0.27"]

[tool.uv]
package = false
```

### 4.5 目录结构

```
aigbooks/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── models.py           # SQLAlchemy ORM
│   │   ├── schemas.py          # Pydantic
│   │   ├── routers/
│   │   │   ├── books.py
│   │   │   ├── reports.py
│   │   │   ├── search.py
│   │   │   └── feed.py            # RSS 订阅
│   │   ├── middleware/
│   │   │   ├── rate_limit.py
│   │   │   └── exception.py
│   │   └── search.py           # PG FTS 查询封装
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── ocr/                # Tesseract.js 封装
│   │   └── api/
│   └── package.json
├── scripts/e2e.sh
├── docs/plans/
└── AGENTS.md
```

---

## 5. 决策记录

| 决策点 | 选择 | 否决方案 | 否决理由 |
|---|---|---|---|
| 用户体系 | 完全匿名 | 注册/登录 | MVP 最小可行，符合"自由举报"精神 |
| 审核 | 无审核 | 阈值审核 / 人工审核 | 用户明确要求"减少使用成本" |
| 数据库 | PostgreSQL | MySQL | PG 内置 FTS 更成熟，避免引入 Meilisearch 等额外组件 |
| 包管理 | uv | pip / poetry | 用户指定；uv 更快、lock 更稳 |
| 后端框架 | FastAPI | Django / Flask | 异步性能 + 类型友好 + 自动 OpenAPI |
| 全文检索 | PG FTS（simple 字典） | Whoosh / Meilisearch | 与 PG 同源，零外部依赖；后续可升级 zhparser |
| OCR | Tesseract.js（客户端） | 服务端 OCR / 云端 OCR | 零成本、隐私好、无服务端压力 |
| 文件存储 | 本地磁盘 | OSS / S3 | MVP 最简，后续可平滑迁移 |
| 投票防刷 | IP + 浏览器指纹 | 完全不防 | 用户明确选择 B（指纹） |
| 举报限流 | 每 (IP+指纹) 每小时 5 条 | 无限制 | 防止恶意刷库 |
| UI 库 | Naive UI | Element Plus | TS 原生、bundle 更小 |
| RSS 订阅 | `feedgen` 输出 RSS 2.0（20 条） | 手写 XML | 库成熟，零模板依赖 |

---

## 6. 后续扩展（不在 MVP 范围）

- zhparser 升级中文分词精度
- 举报趋势统计 / 排行榜
- R2 / S3 对象存储迁移
- Cloudflare Turnstile 验证码
- PWA 离线缓存
- 多语言支持

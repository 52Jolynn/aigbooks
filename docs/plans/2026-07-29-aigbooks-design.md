# AIGBooks 产品设计文档

---
创建时间: 2026-07-29 17:20
最后更新: 2026-08-02 16:05（通用编号标识符扩展：ISBN + ISSN）
状态: 已完成（实施中）
---

## 0. 一句话定位

**AIGBooks** = 一个**只读匿名 + 自由举报**的"AI 生成内容黑名单"网站，让读者在购书/订阅前快速识别并避开 AI 生成的劣质图书与期刊。

无账号体系、不留存任何举报人身份、零审核。

---

## 1. 产品形态与用户流程

### 1.1 读者（默认匿名访客）

1. 首页看到**最新 20 条举报**（按 `reports.created_at DESC` 排序），前端渲染为 1 条 Featured + 18 条 ReportCard（共 19 条可视，第 20 条预留扩展）
2. 顶部搜索框：题名 / 作者 / 编号（ISBN 或 ISSN）**或**举报描述全文（PG FTS 模糊匹配）
3. 点开某编号：聚合该 ISBN/ISSN 的全部举报 + 总举报次数 + 每条证据（图片/视频/文字）+ 点赞/点踩

### 1.2 举报人（同一匿名入口）

1. 点击导航或浮动按钮跳转 `/report` 独立路由（中央 720px 表单页）
2. 必填：**编号类型（ISBN/ISSN）+ 编号值、题名、作者、举报描述**
3. 可选：**封面图**（默认占位图）、**证据**（图片/视频，可多份；文字证据即描述字段）
4. 表单支持 **Tesseract.js 客户端 OCR**：扫 ISBN 条形码 / ISSN 条码 / 书脊照片 → 自动回填三项
5. 提交即生效，无审核；触发限流时返回 429

### 1.3 标识符体系

AIGBooks 采用通用的 `(type, identifier)` 二元组作为聚合根，支持：

| type | 含义 | 校验正则（归一化后） |
|---|---|---|
| `isbn` | 图书（ISBN-10 或 ISBN-13） | `/^(?:\d{9}[\dX]|\d{13})$/` |
| `issn` | 期刊/连续出版物（ISSN-8） | `/^\d{4}-?\d{3}[\dX]$/` |
| `issn-l` | 链接 ISSN（纸电版合并标识，**当前仅 enum 预留**） | `/^\d{4}-?\d{3}[\dX]$/` |

> 设计要点：ISBN 与 ISSN 形态不冲突（10/13 位 vs 8 位），但同一字符串（如"1003-7055"）可能既是 ISBN 又是 ISSN。系统按 `(type, identifier)` 联合唯一去重，不同 type 的同一字符串视为不同聚合根。

### 1.4 MVP 不做（YAGNI）

- ❌ 登录 / 注册 / 昵称
- ❌ 举报人工审核
- ❌ 举报端防滥用限流（仅 IP+指纹限流，不做语义审核）
- ❌ 外部 API 自动补全封面/简介
- ❌ 推荐榜单 / 可信作者榜单
- ❌ 评论 / 回复
- ❌ 举报内容去重（仅按编号自动聚合）
- ❌ ISSN-L 业务识别（type 枚举预留，前端表单不暴露）

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
| `GET`  | `/api/identifiers/recent` | 最新 20 条举报 |
| `GET`  | `/api/search?q=` | 题名/作者/编号 + 描述全文检索 |
| `GET`  | `/api/identifiers/{type}/{identifier}` | 单编号详情 + 全举报聚合 |
| `POST` | `/api/reports` | 提交举报（含 multipart 文件；表单字段：`type` + `identifier`） |
| `POST` | `/api/reports/{id}/vote` | 点赞/点踩（IP + 指纹） |
| `GET`  | `/api/feed/reports.rss` | RSS 2.0 订阅最新 20 条举报 |

> **路径变更说明**（2026-08-02）：原 `/api/books/{isbn}` 重构为 `/api/identifiers/{type}/{identifier}`。旧 URL **不保留**（用户已确认放弃兼容）。

### 2.4 PostgreSQL FTS 设计

- `identifiers.title` + `identifiers.author` → 触发器同步至 `identifiers.tsv_meta`（带 weight）
- `reports.description` → 同步至 `reports.tsv_desc`
- 搜索时用 `to_tsquery('simple', $1)` 命中两个 tsvector 并 `union`
- 中文分词先用 PG 内置 `simple` 字典（按字符切）；后续按需升级 `zhparser`

### 2.5 RSS 订阅设计

- **端点**：`GET /api/feed/reports.rss`，`Content-Type: application/rss+xml; charset=utf-8`
- **条数**：最新 20 条（与首页一致）
- **排序**：`reports.created_at DESC`
- **关联**：每条 item 链接到该编号详情页 `/identifiers/{type}/{identifier}`，并附原举报描述作 `<description>`
- **库**：`feedgen`（mature、零模板依赖，输出 RSS 2.0 / Atom 双格式）
- **缓存**：MVP 不缓存，每次请求实时生成；后续可加 `Cache-Control: max-age=300`
- **Nginx**：`location = /api/feed/reports.rss { add_header Content-Type "application/rss+xml; charset=utf-8"; }` 兜底 MIME

**item 字段映射：**

| RSS 字段 | 数据源 |
|---|---|
| `<title>` | `[{type}:{identifier}] {title} — {author}` |
| `<link>` | `https://{host}/identifiers/{type}/{identifier}` |
| `<guid>` | `report-{id}`（保证全局唯一） |
| `<pubDate>` | `reports.created_at`（RFC822） |
| `<description>` | `reports.description`（CDATA 包裹防转义） |

---

## 3. 数据模型

```sql
-- 聚合根（按 (type, identifier) 联合唯一）
-- type ∈ {'isbn', 'issn', 'issn-l'}，支持图书 / 期刊 / 连续出版物
CREATE TABLE identifiers (
    id           BIGSERIAL PRIMARY KEY,
    type         VARCHAR(16) NOT NULL DEFAULT 'isbn',  -- 标识符类型
    identifier   TEXT NOT NULL,                       -- 编号本体（ISBN/ISSN 字面量）
    title        TEXT NOT NULL,
    author       TEXT NOT NULL,
    cover_path   TEXT,                                 -- 相对路径 `covers/{type}/{identifier}{ext}`
    report_count INT NOT NULL DEFAULT 0,
    tsv_meta     TSVECTOR,                             -- title(A) + author(B) 加权
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (type, identifier)
);
CREATE INDEX identifiers_tsv_meta_idx ON identifiers USING GIN(tsv_meta);
CREATE INDEX identifiers_type_identifier_idx ON identifiers (type, identifier);

-- 举报（每条独立展示，关联 identifiers；含 IP+指纹用于限流）
CREATE TABLE reports (
    id            BIGSERIAL PRIMARY KEY,
    identifier_id BIGINT NOT NULL REFERENCES identifiers(id) ON DELETE CASCADE,
    description   TEXT NOT NULL,                    -- 举报描述，搜索源
    tsv_desc      TSVECTOR,                         -- 描述全文检索
    upvote        INT NOT NULL DEFAULT 0,
    downvote      INT NOT NULL DEFAULT 0,
    ip            INET NOT NULL,                    -- 限流 + 审计（不展示）
    fingerprint   TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX reports_tsv_desc_idx    ON reports USING GIN(tsv_desc);
CREATE INDEX reports_identifier_id_idx ON reports(identifier_id);
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
- **联合唯一**：`(type, identifier)` 联合唯一 → 同一 type 内编号去重，不同 type 视为不同聚合根
- **投票唯一**：`(report_id, ip, fingerprint)` 复合唯一 → 同一访客对同一举报仅一票，再次投票覆盖
- **聚合计数**：`identifiers.report_count` 由 reports INSERT/DELETE 触发器维护
- **检索**：两张 tsvector 列由 AFTER INSERT/UPDATE 触发器维护
- **限流**：直接查 `reports` 表，`WHERE ip=? AND fingerprint=? AND created_at >= now() - interval '1 hour'` → 若 `count >= 5` 则拒绝

### 3.2 文件存储路径

- 封面：`/var/lib/aigbooks/covers/{type}/{identifier}.{ext}`（按 type 子目录，避免 ISBN/ISSN 编号意外碰撞）
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
| 编号重复提交 | `INSERT ... ON CONFLICT (type, identifier) DO UPDATE` → 自动聚合复用 identifiers |
| 编号格式错误 | 后端按 type 选择正则校验，不通过返回 422 |
| 不支持的 type（如 `doi`） | 路由层校验失败返回 422 |
| OCR 失败 / 识别错误 | 前端捕获回退手填，不阻塞提交 |
| 文件超限（单文件 20MB） | 后端校验返回 413 |
| 文件类型非法（仅 jpg/png/webp/mp4） | 后端 MIME 校验返回 415 |
| 限流触发 | 返回 429，UI 弹"请稍后再试" |
| 搜索空结果 | 前端展示"暂无相关举报" |
| 后端异常 | 全局中间件统一 JSON `{code, msg}`，避免堆栈泄漏 |

### 4.2 测试策略

- **后端**：pytest + httpx AsyncClient（62 用例）
  - 关键用例：ISBN/ISSN 双轨举报聚合、跨类型隔离、限流（连发 6 条第 6 条 429）、搜索命中 tsvector / FTS5、投票唯一约束、文件上传校验、ISBN/ISSN 格式校验、type 不在枚举
- **前端**：Vitest + Vue Test Utils
  - 关键用例：表单校验（含三套正则）、OCR 三套正则（ISBN 优先级 > ISSN）、搜索防抖、投票状态切换
- **E2E**：`scripts/e2e.sh` + `pytest -m e2e` 双轨烟测
  - 关键链路：举报（ISBN）→ 聚合 → 详情 → 投票；举报（ISSN）→ 聚合 → 详情；RSS 含双轨

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
│   │   │   ├── identifiers.py  # 聚合根路由（recent + {type}/{identifier}）
│   │   │   ├── reports.py
│   │   │   ├── search.py
│   │   │   └── feed.py         # RSS 订阅
│   │   ├── middleware/
│   │   │   ├── rate_limit.py
│   │   │   └── exception.py
│   │   ├── db/
│   │   │   ├── constants.py    # DIALECT_* + IdentifierType 常量
│   │   │   ├── search/         # SQLite FTS5 / PG websearch / MySQL ngram
│   │   │   └── upsert.py       # 跨方言 UPSERT 工厂
│   │   └── search.py           # 全文检索封装
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_init.py
│   │       └── 002_rename_books_to_identifiers.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── IdentifierDetailView.vue  # 聚合根详情（原 BookDetailView）
│   │   ├── components/
│   │   ├── ocr/                # Tesseract.js 封装（含 ISBN+ISSN 双正则）
│   │   └── api/
│   │       └── identifiers.ts  # 聚合根 API（原 books.ts）
│   └── package.json
├── scripts/e2e.sh
├── docs/plans/
│   ├── 2026-07-29-aigbooks-design.md
│   ├── 2026-07-30-aigbooks-implementation-v2.md
│   └── 20260802_通用编号标识符实施计划.md
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
| 首页排序 | 按 `reports.created_at DESC` 最新举报优先 | 按 `books.report_count DESC` 热门书籍优先 | v2 澄清：与"最新 20 条举报"产品语义一致 |
| 首页响应结构 | `ReportOut[]`（每条含 book 摘要） | `BookOut[]` | v2 澄清：报告维度更细，含描述/票数 |
| 首页显示数量 | 1 Featured + 18 Grid = 19 条 | 1 + 19 = 20 条 | v2 澄清：3 列 × 6 行视觉稳定 |
| 举报入口 | 独立路由 `/report`（720px 表单） | 首页弹窗 Modal | v2 澄清：与 UI 设计一致 |
| 投票再次点击 | 同方向保持 + 反方向切换 | 再次点击取消 | v2 澄清：与 `ON CONFLICT DO UPDATE` 一致 |
| 字体加载 | Fontsource 自托管 | Google Fonts CDN | v2 澄清：离线可用、生产稳定 |
| 隐私策略 | IP + fingerprint 原值保留 | 入库前 SHA256 哈希 | v2 澄清：哈希后无法做限流窗口判定 |
| ORM relationship | 使用 `relationship` + `lazy="raise"` | 不声明 relationship | selectinload 必须依赖；lazy="raise" 防止 async 模式下隐式懒加载异常 |
| 聚合根标识符 | `(type, identifier)` 二元组，type ∈ {isbn, issn, issn-l} | 单一 ISBN 字段 | 2026-08-02 扩展：支持期刊/连续出版物（ISSN）；扁平、易扩展未来 DOI/arXiv ID |
| URL 形态 | `/api/identifiers/{type}/{identifier}` | `/api/books/{isbn}` | 2026-08-02 重构：RESTful 语义更准；旧 URL 不保留 |
| 封面存储 | `covers/{type}/{identifier}{ext}` 子目录 | 平铺 `covers/{isbn}{ext}` | 2026-08-02 重构：防 ISBN/ISSN 编号意外碰撞 |

---

## 6. 后续扩展（不在 MVP 范围）

- zhparser 升级中文分词精度
- 举报趋势统计 / 排行榜
- R2 / S3 对象存储迁移
- Cloudflare Turnstile 验证码
- PWA 离线缓存
- 多语言支持
- DOI / arXiv ID 等其他学术标识符（仅需新增 `IdentifierType` 常量 + 正则映射）
- ISSN-L 业务识别（链接 ISSN，纸电版合并聚合）

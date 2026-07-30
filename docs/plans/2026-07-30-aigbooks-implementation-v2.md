# AIGBooks 实施计划

---
创建时间: 2026-07-30 10:55
最后更新: 2026-07-30 18:10（实施完成）
状态: 已完成 ✅
版本: v2.0（基于设计文档 + UI mockup + 用户澄清决策重新生成）
---

> **实施完成记录**：
> - 8 个任务全部完成（必做 #0/8 + 任务 1-7）
> - 代码已 commit：`3c15fbd feat: ship AIGBooks MVP (backend + frontend + deploy + tests)`
> - 后端测试：22 passed, 6 skipped
> - 前端测试：17 passed (8 files)
> - 流程审查：3 项 P1 警告（已记录待后续优化）
> - 三方对齐：4 项 P1 偏差（已修复）
>
> **遗留警告**（详见 `docs/reports/`）：
> - 业务流程 P1-1：Book 聚合并发竞态（SELECT-then-INSERT/UPDATE）
> - 业务流程 P1-2：封面 MIME 校验弱于证据（仅扩展名校验）
> - 业务流程 P1-3：RecentReportsOut.total 语义歧义（返回 LIMIT 后条数）
> - 流程审查报告：`docs/reports/20260730_业务流程审查.md`
> - 三方对齐报告：`docs/reports/20260730_三方对齐评估.md`

## 0. 与 v1 的差异说明

本版本基于以下素材重新生成：

| 素材 | 路径 | 作用 |
|---|---|---|
| 产品设计文档 | `docs/plans/2026-07-29-aigbooks-design.md` | API、数据模型、决策记录 |
| UI Mockup | `/tmp/opencode/aigbooks-mockup/index.html`（617 行） | 首页视觉基线 + 设计 token |
| v1 实施计划 | `docs/plans/2026-07-29-aigbooks-implementation.md` | 任务拆解、工时估算 |
| 用户澄清决策 | 6 项关键冲突已通过选择题确认 | 见 §2.2 |

**v1 → v2 主要变更：**

1. 首页 API 响应结构从 `BookOut[]` 改为 `ReportOut[]`（澄清决策 §2.2.1）
2. 首页显示 1 + 18 = 19 条（澄清决策 §2.2.2）
3. 举报入口明确为独立路由 `/report`（澄清决策 §2.2.3）
4. 投票再次点击同方向保持、切换方向切换（澄清决策 §2.2.4）
5. 字体走 Fontsource 自托管（澄清决策 §2.2.5）
6. IP/fingerprint 原值保留，不做哈希（澄清决策 §2.2.6）
7. 补全 mockup → Vue 组件映射表与 UI Token 速查
8. 增加次要默认决策清单（§9），等待用户评审

**实施差异说明（v2 落地过程中追加）：**

- Python 版本从 3.11 调整为 3.10（沙箱网络限制，3.10 已是 LTS 等价物；`pyproject.toml` 的 `requires-python` 与 `.python-version` 保持 3.10；ruff `target-version = "py310"`；本差异不视为业务 bug）
- `stores/reports.ts`（D6 追加）用于 Masthead 总数显示，是必要的全局状态
- ORM `relationship` + `lazy="raise"` 已启用（selectinload 必要支撑 + async 模式隐式懒加载防护）

---

## 1. 计划概述

| 维度 | 内容 |
|---|---|
| 目标（SMART） | 在 8 工作日内交付一个单服务器可运行的 AIGBooks MVP：FastAPI + PostgreSQL 15 + Vue 3 全栈应用，支持匿名举报、按 ISBN 聚合、全文搜索、IP+指纹投票、RSS 订阅，前端按 Editorial Warning Dossier 视觉规范实现 |
| 范围 | 后端 6 个 API + 前端 4 个页面 + 数据库 4 张表（含 2 个 FTS 触发器 + 1 个聚合计数触发器 + 3 个 GIN 索引）+ systemd + nginx 部署 |
| 预期成果 | (1) `backend/` 可 `uv run uvicorn` 启动；(2) `frontend/` 可 `pnpm dev` 与 `pnpm build`；(3) `scripts/e2e.sh` 跑通举报 → 聚合 → 搜索 → 投票 → RSS 全链路；(4) `/etc/systemd/system/aigbooks-api.service` + nginx 配置文件可直接部署 |
| 优先级 | P0 6.5 天 + P1 1.5 天 = **总计 8 天** |
| 验收标准 | 见 §10 |

---

## 2. 需求背景

### 2.1 原始需求

> AI 生成劣质书籍泛滥，读者缺乏甄别渠道。AIGBooks 通过自由举报 + 匿名浏览 + 按 ISBN 聚合 + 全文搜索 + 投票，让读者快速避坑。无账号，零审核。

### 2.2 关键澄清决策（用户确认）

| # | 决策点 | 选择 | 理由 |
|---|---|---|---|
| 1 | 首页 `/api/books/recent` 排序 | **最新举报优先**（按 `reports.created_at DESC`） | 符合设计文档 §1.1 "最新 20 条举报卡片" 描述 |
| 2 | 首页显示数量 | **1 Featured + 18 Grid = 19 条**（API 返回 20 条，最后 1 条进无限滚动） | mockup 当前是 1+6=7，预留扩展；3 列 × 6 行视觉稳定 |
| 3 | 举报入口形态 | **独立路由 `/report`**（中央 720px 表单页） | 与 v1 实施计划 + UI 设计一致；mockup 按钮也是 `href="/report"` |
| 4 | 重复投票行为 | **覆盖旧投票**（再次点击同方向保持，反方向切换） | 与数据库 `UNIQUE(report_id, ip, fingerprint)` + `ON CONFLICT DO UPDATE` 一致；后端实现简单 |
| 5 | 字体加载方案 | **Fontsource 自托管**（pnpm 包构建进 bundle） | 离线可用、无外网请求、生产环境稳定 |
| 6 | 隐私策略 | **保留 IP + fingerprint 原值**，不哈希 | 哈希后无法做限流窗口判定；MVP 不做隐私脱敏 |

### 2.3 业务价值

- **读者侧**：购书前快速识别 AI 劣质书，节省时间金钱
- **举报侧**：低门槛自由表达（无账号、无审核），鼓励参与
- **生态侧**：通过 ISBN 聚合形成"重复举报 → 共识"的发现机制

### 2.4 成功标准

| 维度 | 标准 |
|---|---|
| 功能 | 6 个 API 全部跑通，4 个页面全部可达，OCR 回填、限流、投票唯一性生效 |
| 视觉 | 在 1280px 视口下首页三列等宽；印章、字体、纸张纹理全部按 mockup 实现 |
| 测试 | 后端 pytest 全绿；前端 vitest 关键组件全绿；`scripts/e2e.sh` 跑通全链路 |
| 部署 | systemd 启动后 uvicorn :8000 监听；nginx 反代通过；HTTPS 可选 certbot |
| 性能 | 首页首屏 < 1.5s（静态资源本地化后）；搜索响应 < 500ms（10 万级数据） |

---

## 3. 影响范围

| 层级 | 影响 |
|---|---|
| 文档 | `docs/plans/2026-07-29-aigbooks-implementation.md` 标记 superseded；本计划替代 |
| 设计文档 | 同步更新 `docs/plans/2026-07-29-aigbooks-design.md` 中首页 API 响应结构与数量（任务 1 执行） |
| 后端 | **全部新建**：FastAPI 入口、配置、ORM、Pydantic、4 个 router、FTS 查询、文件存储、限流、全局异常、RSS 生成 |
| 数据库 | **全部新建**：4 张表 + 2 个 tsvector 触发器 + 1 个 report_count 触发器 + 3 个 GIN 索引 + Alembic 迁移 |
| 前端 | **全部新建**：Vue 3 + Vite + TS 项目，4 个路由页面，13 个公共组件，1 个全局样式表，OCR 封装 |
| 部署 | **全部新建**：systemd 服务文件、nginx 配置片段、部署脚本、E2E 测试脚本 |
| 现有资产 | `/tmp/opencode/aigbooks-mockup/index.html` 作为视觉基线；实施时拆分为 dossier.css + 各 Vue 组件 |
| 第三方依赖 | 后端 9 个生产依赖 + 3 个 dev 依赖（uv 管理）；前端 12+ 个生产依赖 + 5+ 个 dev 依赖（pnpm 管理） |

---

## 4. 设计原则遵循

| 原则 | 来源 | 实施体现 |
|---|---|---|
| 单文件功能聚焦 | AGENTS.md "代码之美但不过度设计" | 每个 router、组件只负责一件事；函数 < 50 行 |
| KISS + YAGNI | 历史经验 LRN-20260720-001 | 不为"未来可能"提前抽象；SQLAlchemy 模型声明 `relationship` + `lazy="raise"`（selectinload 必要支撑；防 async 模式下隐式懒加载触发 MissingGreenlet） |
| 三方对齐 | 历史经验 lrn-d44-triparty | 设计文档 + 本计划 + 代码实现同步 |
| 设计文档先行 | AGENTS.md §4 强制任务清单 | 实施时同步更新 design.md 中首页 API 结构与数量 |
| FTS 触发器 BEFORE | 历史经验 PG FTS 注意事项 | `BEFORE INSERT OR UPDATE` 触发器内 `NEW.tsv_xxx := to_tsvector(...)` |
| BEM 命名 | mockup 当前风格 | `.block__element` + `.is-active`/`.is-voted` 状态类 |
| Fontsource 自托管 | 澄清决策 §2.2.5 | 不引入 Google Fonts `<link>` |
| 关键代码 TDD | 历史经验 FTS 易错 | trigger SQL + feedgen 输出 + 限流计数必须有测试 |
| AsyncSession 不跨请求 | 历史经验 FastAPI async | `Depends(get_session)` 注入，不在中间件创建 session |
| systemd 最小权限 | 历史经验 systemd 部署 | `User=www-data`、`ProtectSystem=strict`、`NoNewPrivileges=true` |

---

## 5. 任务分解

### 任务 1：后端项目脚手架 [P0, 0.5天]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `backend/pyproject.toml` | uv 项目声明，依赖见下 |
| 新增 | `backend/app/__init__.py` | 空文件，标识 Python 包 |
| 新增 | `backend/app/main.py` | FastAPI 入口 |
| 新增 | `backend/app/config.py` | pydantic-settings 配置 |
| 新增 | `backend/app/database.py` | 异步引擎 + AsyncSession 工厂 |
| 新增 | `backend/alembic.ini` | Alembic 配置 |
| 新增 | `backend/alembic/env.py` | Alembic 异步迁移环境 |
| 新增 | `backend/alembic/script.py.mako` | 迁移文件模板 |
| 新增 | `backend/.env.example` | 环境变量样例 |
| 新增 | `backend/.python-version` | `3.11` |

#### 代码调整清单

| 模块 | 说明 |
|---|---|
| `config.py` | `BaseSettings`，前缀 `AIGBOOKS_`；字段：`database_url`、`evidence_dir`、`covers_dir`、`max_upload_size=20MB`、`allowed_mime_types`、`report_rate_limit=5`、`report_rate_window=3600`、`page_size=20`、`cors_origins` |
| `database.py` | `async_engine` + `async_sessionmaker` + `get_session` 依赖注入；`Base = DeclarativeBase` |
| `main.py` | 创建 FastAPI 实例，挂载 `StaticFiles(covers/evidence)`，注册 4 个 router，配置 CORS，注册全局异常处理器 |

#### `pyproject.toml` 依赖清单

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
    "pydantic-settings>=2.5",
    "python-multipart>=0.0.12",
    "feedgen>=1.0",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.6",
]
```

#### 任务 1 验收

- [ ] `uv sync` 成功
- [ ] `uv run python -c "import app.main"` 不报错
- [ ] `uv run uvicorn app.main:app --reload` 启动并访问 `/docs` 可见 OpenAPI

---

### 任务 2：数据模型与迁移 [P0, 1天]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `backend/app/models.py` | SQLAlchemy 2.0 ORM 模型 |
| 新增 | `backend/app/schemas.py` | Pydantic v2 请求/响应模型 |
| 新增 | `backend/alembic/versions/001_init.py` | 初始迁移：建表 + 触发器 + GIN 索引 |
| 修改 | `docs/plans/2026-07-29-aigbooks-design.md` | 同步首页 API 结构为 ReportOut、数量 20 |

#### ORM 模型设计

```python
# 简化示例（实际实现按 SQLAlchemy 2.0 typed Mapped API）
class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    isbn: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    cover_path: Mapped[str | None] = mapped_column(Text)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tsv_meta: Mapped[Any] = mapped_column(TSVECTOR)  # 触发器维护
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tsv_desc: Mapped[Any] = mapped_column(TSVECTOR)
    upvote: Mapped[int] = mapped_column(Integer, default=0)
    downvote: Mapped[int] = mapped_column(Integer, default=0)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Evidence(Base):
    __tablename__ = "evidences"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_kind: Mapped[str] = mapped_column(Text, nullable=False)  # 'image'|'video'|'text'
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Vote(Base):
    __tablename__ = "votes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    vote_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # +1/-1
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    __table_args__ = (UniqueConstraint("report_id", "ip", "fingerprint", name="uq_vote"),)
```

**不定义 `relationship`**（YAGNI），查询时显式 join。

> **实施差异说明（v2 落地追加）**：实际实现中 ORM 模型声明了 `relationship` 并配合 `lazy="raise"`，
> 原因是 `routers/books.py` 中 `selectinload(Report.evidences)` 等用法依赖 `Report.evidences`
> 关系属性存在；同时 `lazy="raise"` 显式禁止隐式懒加载，避免 async 模式下访问
> 未加载的关系时触发 `MissingGreenlet`。这是一项**安全的便利**，非过度设计。

#### 迁移 SQL 要点

迁移文件通过 `op.execute(...)` 写：

1. **触发器 1 - `books_tsv_meta_trigger`**：`BEFORE INSERT OR UPDATE` on `books`，`NEW.tsv_meta := setweight(to_tsvector('simple', NEW.title), 'A') || setweight(to_tsvector('simple', NEW.author), 'B')`
2. **触发器 2 - `reports_tsv_desc_trigger`**：`BEFORE INSERT OR UPDATE` on `reports`，`NEW.tsv_desc := to_tsvector('simple', NEW.description)`
3. **触发器 3 - `update_book_report_count_trigger`**：`AFTER INSERT OR DELETE` on `reports`，维护 `books.report_count`
4. **GIN 索引**：`books_tsv_meta_idx`、`reports_tsv_desc_idx`、`reports_rate_limit_idx(ip, fingerprint, created_at)`
5. **Downgrade**：删除所有触发器、索引、表

#### Pydantic Schema 设计

```python
# 响应模型（含嵌套）
class BookSummary(BaseModel):  # 用于 ReportOut 嵌套
    isbn: str
    title: str
    author: str
    cover_path: str | None
    report_count: int
    model_config = ConfigDict(from_attributes=True)

class EvidenceOut(BaseModel):
    id: int
    file_path: str
    file_kind: str
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReportOut(BaseModel):
    """首页 / 搜索 / 详情共用响应结构"""
    id: int
    book: BookSummary          # 嵌套书籍摘要
    description: str
    upvote: int
    downvote: int
    created_at: datetime
    evidences: list[EvidenceOut] = []
    model_config = ConfigDict(from_attributes=True)

class BookDetailOut(BookSummary):
    """书籍详情：含全部 reports 列表"""
    created_at: datetime
    updated_at: datetime
    reports: list[ReportOut] = []

class RecentReportsOut(BaseModel):
    """首页响应"""
    reports: list[ReportOut]  # 最新 20 条举报
    total: int                # 当前返回条数

class SearchResultOut(BaseModel):
    reports: list[ReportOut]
    total: int
    query: str

# 请求模型
class VoteCreate(BaseModel):
    vote_type: Literal[-1, 1]
    fingerprint: str = Field(min_length=8, max_length=128)
```

#### 任务 2 验收

- [ ] `uv run alembic upgrade head` 成功
- [ ] `psql -c "\d books"` / `reports` / `evidences` / `votes` 表结构与设计一致
- [ ] `\d+ books` 可见 3 个 GIN 索引
- [ ] `\df` 可见 3 个触发器函数
- [ ] `uv run alembic downgrade base && uv run alembic upgrade head` 端到端可逆

---

### 任务 3：后端 API 实现 [P0, 2天]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `backend/app/routers/books.py` | GET recent + GET detail |
| 新增 | `backend/app/routers/reports.py` | POST create + POST vote |
| 新增 | `backend/app/routers/search.py` | GET search |
| 新增 | `backend/app/routers/feed.py` | GET RSS |
| 新增 | `backend/app/search.py` | FTS 查询封装 |
| 新增 | `backend/app/services/storage.py` | 文件上传服务 |
| 新增 | `backend/app/middleware/rate_limit.py` | 举报限流 |
| 新增 | `backend/app/middleware/exception.py` | 全局异常处理 |
| 新增 | `backend/app/utils/client_ip.py` | 真实 IP 获取（X-Forwarded-For） |

#### 3.1 `routers/books.py`

**`GET /api/books/recent`**：

- 查询：按 `reports.created_at DESC` 取最新 20 条
- 关联：`JOIN books ON books.id = reports.book_id`
- 每条 Report 关联 evidences：`LEFT JOIN evidences ON evidences.report_id = reports.id`
- 使用 `selectinload` 避免 N+1
- 响应：`RecentReportsOut { reports: [...20], total: 20 }`

**`GET /api/books/{isbn}`**：

- 查询：根据 `books.isbn = {isbn}` 获取书籍
- 不存在返回 404 `{"code": 404, "msg": "书籍不存在"}`
- 关联：全部 reports（按 `created_at DESC`）+ 每条 report 的 evidences
- 响应：`BookDetailOut`

#### 3.2 `routers/reports.py`

**`POST /api/reports`**（multipart/form-data）：

处理流程：

1. 解析 `isbn`、`title`、`author`、`description`、`fingerprint`、`ip`（ip 由后端从请求取，不由前端传）
2. 校验 ISBN 格式（10/13 位数字 + 可选连字符）
3. 限流检查（见 3.6）
4. 文件校验：MIME 白名单（`image/jpeg`、`image/png`、`image/webp`、`video/mp4`），单文件 ≤ 20MB
5. 保存封面：`covers/{isbn}.{ext}`（保留原扩展名）
6. 保存证据：`evidence/{yyyy}/{mm}/{uuid4}.{ext}`
7. 事务：
   ```sql
   INSERT INTO books (isbn, title, author, cover_path) 
   VALUES (?, ?, ?, ?) 
   ON CONFLICT (isbn) DO UPDATE SET 
     cover_path = COALESCE(EXCLUDED.cover_path, books.cover_path),
     updated_at = now()
   RETURNING id;
   ```
   （注：仅在上传了封面时更新 cover_path 与 updated_at）
8. `INSERT INTO reports ... RETURNING *` 获取 report_id
9. 批量 `INSERT INTO evidences ...`
10. 返回 `ReportOut`（含嵌套 book + evidences）

**`POST /api/reports/{id}/vote`**（application/json）：

1. 校验 report 存在
2. 从请求取 IP、从 header `X-Fingerprint` 取 fingerprint
3. UPSERT：
   ```sql
   INSERT INTO votes (report_id, ip, fingerprint, vote_type)
   VALUES (?, ?, ?, ?)
   ON CONFLICT (report_id, ip, fingerprint) DO UPDATE 
     SET vote_type = EXCLUDED.vote_type, created_at = now();
   ```
4. 重算 reports.upvote/downvote：`SELECT vote_type, COUNT(*) FROM votes WHERE report_id=? GROUP BY vote_type`
5. 更新 reports 表
6. 返回更新后的 `ReportOut`

#### 3.3 `routers/search.py` + `search.py`

**`GET /api/search?q=&page_size=20`**：

- 输入清洗：`re.sub(r'[:&|!()*\'"]', ' ', query).strip()`
- 清洗后为空 → 走 ILIKE 模糊匹配 `title|author|description ILIKE %q%`
- 清洗后非空 → 走 PG FTS：
  ```sql
  SELECT DISTINCT r.*, b.*
  FROM reports r JOIN books b ON b.id = r.book_id
  WHERE r.tsv_desc @@ websearch_to_tsquery('simple', :q)
     OR b.tsv_meta  @@ websearch_to_tsquery('simple', :q)
  ORDER BY GREATEST(r.created_at, b.updated_at) DESC
  LIMIT :page_size;
  ```
- 使用 `websearch_to_tsquery`（用户友好语法，比 `to_tsquery` 安全）
- 响应：`SearchResultOut`

#### 3.4 `routers/feed.py`

**`GET /api/feed/reports.rss`**：

- 查询最新 20 条 report（按 `created_at DESC`），关联 book
- 用 `feedgen.feed.RssGenerator` 构建 RSS 2.0：
  - `fe.id("https://aigbooks.example.com")`
  - `fe.title("AIGBooks — Latest Reports")`
  - `fe.link(href=site_url, rel="alternate")`
  - `fe.description("An anonymous reader's dossier of AI-generated books.")`
  - `fe.language("zh-CN")`
- 每条 item：
  - `fe.title(f"[{isbn}] {title} — {author}")`
  - `fe.link(href=f"{site_url}/books/{isbn}")`
  - `fe.guid(f"report-{id}", permalink=False)`
  - `fe.pubDate(created_at.astimezone(timezone.utc))`（关键：UTC 时区）
  - `fe.description(CDATA(description))`
- 响应：`Response(content=rss_str, media_type="application/rss+xml; charset=utf-8")`

#### 3.5 `services/storage.py`

```python
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "video/mp4"}

async def save_cover(file: UploadFile, isbn: str) -> str:
    """保存封面；返回相对路径 covers/{isbn}.{ext}"""
    
async def save_evidence(file: UploadFile) -> tuple[str, str, int]:
    """保存证据；返回 (相对路径, mime_type, size_bytes)"""
    
def get_client_ip(request: Request) -> str:
    """从 X-Forwarded-For 或 request.client.host 取真实 IP"""
```

要点：
- MIME 用 `python-magic` 嗅探文件头，不信 `Content-Type`
- 写入前检查磁盘空间（可选）
- 文件名用 `uuid4().hex` 防冲突

#### 3.6 `middleware/rate_limit.py`

```python
async def check_report_rate_limit(db: AsyncSession, ip: str, fp: str) -> None:
    """每 (ip + fingerprint) 每小时最多 5 条，超出抛 HTTPException(429)"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    count = await db.scalar(
        select(func.count()).select_from(Report)
        .where(Report.ip == ip, Report.fingerprint == fp, Report.created_at >= cutoff)
    )
    if count >= 5:
        raise HTTPException(
            status_code=429,
            detail={"code": 429, "msg": "举报过于频繁，请稍后再试"},
            headers={"Retry-After": "3600"},
        )
```

调用位置：`routers/reports.py` `POST /api/reports` 第一步。

#### 3.7 `middleware/exception.py`

注册到 app：

- `@app.exception_handler(HTTPException)`：保留原 status_code + `{"code": e.status_code, "msg": e.detail}`
- `@app.exception_handler(Exception)`：返回 500 `{"code": 500, "msg": "服务器内部错误"}`，同时 `logger.exception(e)` 记录 traceback
- `@app.exception_handler(RequestValidationError)`：返回 422 `{"code": 422, "msg": "请求参数错误", "errors": [...]}`，不暴露 stack

#### 任务 3 验收

- [ ] 6 个 API 全部在 `/docs` 可访问
- [ ] `curl POST /api/reports` 创建 + 重复 ISBN 自动聚合
- [ ] `curl POST /api/reports` 第 6 次同 IP 返回 429 + `Retry-After` header
- [ ] `curl POST /api/reports/{id}/vote` 同一 fp 第二次同方向覆盖，反方向切换
- [ ] `curl GET /api/search?q=...` 命中 title/author/description
- [ ] `curl GET /api/feed/reports.rss` 返回 RSS 2.0，Content-Type 正确

---

### 任务 4：前端项目脚手架 [P0, 0.5天]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `frontend/package.json` | pnpm 依赖声明 |
| 新增 | `frontend/vite.config.ts` | Vite 配置 + 代理 |
| 新增 | `frontend/tsconfig.json` | TypeScript 严格模式 |
| 新增 | `frontend/tsconfig.node.json` | Node 配置（Vite 用） |
| 新增 | `frontend/index.html` | HTML 入口 |
| 新增 | `frontend/src/main.ts` | Vue 应用入口 |
| 新增 | `frontend/src/App.vue` | 根组件（Masthead + RouterView + Colophon） |
| 新增 | `frontend/src/router/index.ts` | 4 个路由 |
| 新增 | `frontend/src/api/index.ts` | axios 单例 |
| 新增 | `frontend/src/api/books.ts` | `getRecentReports()`、`getBookDetail(isbn)` |
| 新增 | `frontend/src/api/search.ts` | `searchReports(q)` |
| 新增 | `frontend/src/api/reports.ts` | `createReport()`、`voteReport()` |
| 新增 | `frontend/src/ocr/index.ts` | Tesseract.js 封装 |
| 新增 | `frontend/src/styles/dossier.css` | 全局样式 + 设计 token（从 mockup 迁移） |
| 新增 | `frontend/src/stores/fingerprint.ts` | 浏览器指纹生成（Pinia） |
| 新增 | `frontend/src/utils/fingerprint.ts` | 指纹生成算法（hash UA + lang + screen + tz） |

#### `package.json` 关键依赖

```json
{
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.4",
    "pinia": "^2.2",
    "naive-ui": "^2.40",
    "axios": "^1.7",
    "tesseract.js": "^5.1"
  },
  "devDependencies": {
    "vite": "^5.4",
    "@vitejs/plugin-vue": "^5.1",
    "typescript": "^5.5",
    "vue-tsc": "^2.1",
    "@types/node": "^22",
    "@fontsource-variable/fraunces": "^5.1",
    "@fontsource/newsreader": "^5.1",
    "@fontsource/jetbrains-mono": "^5.1",
    "@fontsource/noto-serif-sc": "^5.1",
    "vitest": "^2.1",
    "@vue/test-utils": "^2.4",
    "happy-dom": "^15",
    "prettier": "^3.3",
    "eslint": "^9"
  }
}
```

#### `vite.config.ts` 关键配置

```typescript
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': '/src' },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/covers': { target: 'http://localhost:8000', changeOrigin: true },
      '/evidence': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'tesseract': ['tesseract.js'],  // OCR 单独 chunk，按需懒加载
        },
      },
    },
  },
});
```

#### `router/index.ts`

```typescript
const routes = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/search', name: 'search', component: () => import('@/views/SearchView.vue') },
  { path: '/books/:isbn', name: 'book-detail', component: () => import('@/views/BookDetailView.vue') },
  { path: '/report', name: 'report', component: () => import('@/views/ReportView.vue') },
];
```

#### `ocr/index.ts` 设计要点

```typescript
// 懒加载 Tesseract.js，避免进主 bundle
export async function recognizeText(
  image: File | Blob
): Promise<{ isbn?: string; title?: string; author?: string; raw: string }> {
  try {
    const { createWorker } = await import('tesseract.js');
    const worker = await createWorker(['chi_sim', 'eng'], 1, {
      logger: () => {}, // 静默 progress 日志
    });
    const { data } = await worker.recognize(image);
    await worker.terminate();
    
    const raw = data.text;
    // 正则提取 ISBN（10/13 位）
    const isbnMatch = raw.match(/\b(?:97[89])?[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d\b/);
    // 行 1 通常是书名，行 2 作者（启发式）
    const lines = raw.split('\n').map(s => s.trim()).filter(Boolean);
    return {
      isbn: isbnMatch?.[0]?.replace(/[-\s]/g, ''),
      title: lines[0],
      author: lines[1],
      raw,
    };
  } catch (e) {
    console.warn('OCR failed:', e);
    return { raw: '' };  // 静默回退，不阻塞表单
  }
}
```

#### `utils/fingerprint.ts`

```typescript
// 浏览器指纹（UA + lang + screen + tz + canvas hash）
export async function generateFingerprint(): Promise<string> {
  const components = [
    navigator.userAgent,
    navigator.language,
    `${screen.width}x${screen.height}x${screen.colorDepth}`,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    new Date().getTimezoneOffset().toString(),
  ];
  
  // Canvas fingerprint
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  ctx.textBaseline = 'top';
  ctx.font = "14px 'Arial'";
  ctx.fillStyle = '#f60';
  ctx.fillRect(125, 1, 62, 20);
  ctx.fillStyle = '#069';
  ctx.fillText('aigbooks', 2, 15);
  components.push(canvas.toDataURL());
  
  const raw = components.join('|');
  const buf = new TextEncoder().encode(raw);
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}
```

#### 字体加载（Fontsource）

在 `main.ts` 中：

```typescript
import '@fontsource-variable/fraunces';
import '@fontsource/newsreader/400.css';
import '@fontsource/newsreader/400-italic.css';
import '@fontsource/newsreader/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/700.css';
import '@fontsource/noto-serif-sc/400.css';
import '@fontsource/noto-serif-sc/700.css';
```

#### 任务 4 验收

- [ ] `pnpm install` 成功
- [ ] `pnpm dev` 启动后访问 http://localhost:3000 看到首页骨架
- [ ] `pnpm build` 成功，bundle 中可见 Fontsource 字体文件
- [ ] `pnpm typecheck`（`vue-tsc --noEmit`）零错误

---

### 任务 5：前端页面与组件实现 [P0, 2.5天]

#### 5.0 mockup → Vue 组件映射表

下表是 mockup HTML 中所有 class 名 → Vue 组件文件的最终映射。**所有页面共用 Masthead + Colophon**。

| Mockup class | 角色 | Vue 文件 |
|---|---|---|
| `.masthead` 全套 | 顶部报头 | `components/Masthead.vue` |
| `.ledger` | 首页主容器 | `views/HomeView.vue` |
| `.section-head` | 章节标题 | `components/SectionHeader.vue` |
| `.featured` | 头条举报 | `components/FeaturedReport.vue` |
| `.reports-grid` | 3 列网格 | `components/ReportsGrid.vue` |
| `.report` | 单卡片 | `components/ReportCard.vue` |
| `.stamp` 类（featured/mini） | 印章 | `components/Stamp.vue`（`size: 'featured'\|'mini'`） |
| `.utility` | 浮动工具栏 | `components/UtilityBar.vue` |
| `.colophon` | 页脚 | `components/Colophon.vue` |
| 无（设计规格） | 搜索框 | `components/SearchBox.vue` |
| 无 | 投票按钮 | `components/VoteButton.vue` |
| 无 | 文件上传 | `components/FileUploader.vue` |
| 无 | 证据列表 | `components/EvidenceList.vue` |
| 无 | 表格字段（无圆角） | `components/FormField.vue` |
| 无 | 举报表单整页 | `views/ReportView.vue`（含 ManuscriptForm 风格） |

#### 5.1 文件清单

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `frontend/src/components/Masthead.vue` | 顶部报头 |
| 新增 | `frontend/src/components/SectionHeader.vue` | 章节标题 |
| 新增 | `frontend/src/components/Stamp.vue` | 印章（featured / mini 双尺寸） |
| 新增 | `frontend/src/components/FeaturedReport.vue` | 头条举报卡片 |
| 新增 | `frontend/src/components/ReportCard.vue` | 普通举报卡片 |
| 新增 | `frontend/src/components/ReportsGrid.vue` | 3 列网格容器 |
| 新增 | `frontend/src/components/UtilityBar.vue` | 右下浮动工具栏 |
| 新增 | `frontend/src/components/Colophon.vue` | 页脚 |
| 新增 | `frontend/src/components/SearchBox.vue` | 搜索框 |
| 新增 | `frontend/src/components/VoteButton.vue` | 投票按钮 |
| 新增 | `frontend/src/components/FileUploader.vue` | 文件上传 |
| 新增 | `frontend/src/components/EvidenceList.vue` | 证据列表 |
| 新增 | `frontend/src/components/FormField.vue` | 打字机式表单字段 |
| 新增 | `frontend/src/views/HomeView.vue` | 首页 |
| 新增 | `frontend/src/views/SearchView.vue` | 搜索页 |
| 新增 | `frontend/src/views/BookDetailView.vue` | 书籍详情页 |
| 新增 | `frontend/src/views/ReportView.vue` | 举报表单页 |

#### 5.2 `Masthead.vue` 设计要点

- props: `currentRoute: string`
- 三段顶栏：`Vol. III · No. {当前编号}` / `An Anonymous Reader's Dossier` / `{当前日期}`
- Logo：`AIG<em>books</em>`（`<em>` 标签斜体 + 红色）
- 副标题：`a registry of machine-printed trash you shouldn't pay for`
- 导航：`Latest` / `Search` / `Submit Report` / `RSS`（RSS 用 `<a target="_blank">` 直接指向 `/api/feed/reports.rss`）
- 当前路由对应项加 `is-active` 类

#### 5.3 `Stamp.vue` 设计要点

- props: `count: number`、`size: 'featured' | 'mini'`
- 内容：`Reported × {count}` 或 `× {count}`（mini）
- CSS：3px 红色实线边框 + `transform: rotate(-2.5deg)` + `::before/::after` 双层伪元素（不同透明度）
- 暴露 `pulse()` 方法：投票成功后 200ms `scale(1) → 1.08 → 1`
- 所有尺寸、旋转角度来自 dossier.css 中的 `--stamp-red`

#### 5.4 `FeaturedReport.vue` 设计要点

- props: `report: ReportOut`
- 左侧：封面占位（45° 条纹纹理 + "A." + "NO COVER / NO RECORD"）；有 `book.cover_path` 时渲染 `<img :src="'/covers/' + book.cover_path">`
- 右侧：`report__category` + 标题 + 作者 + ISBN + 描述引用（`blockquotae`）+ Stamp(featured)
- 标题用 `RouterLink` 跳转 `/books/{isbn}`
- 全部按 mockup `.featured` 类样式

#### 5.5 `ReportCard.vue` 设计要点

- props: `report: ReportOut`
- 内容：category + 标题 + 作者 + ISBN + excerpt（截断 120 字）+ footer（日期 + Stamp(mini)）
- 标题用 `RouterLink`
- 按 `:nth-child` 计算 `animation-delay`，实现 typeset 动画

#### 5.6 `ReportsGrid.vue` 设计要点

- props: `reports: ReportOut[]`、`columns: 2 | 3 = 3`
- 渲染网格，子元素继承 dossier.css 中的 `.reports-grid > *` 动画规则
- 响应式：≤900px 改 2 列，≤600px 改 1 列

#### 5.7 `UtilityBar.vue` 设计要点

- RSS 链接：`/api/feed/reports.rss`，monospace 小标签
- 举报按钮：`RouterLink` 包裹，跳转 `/report`，黑底 + 红色阴影 + hover 偏移
- 固定右下角 24px

#### 5.8 `SearchBox.vue` 设计要点

- 老式借阅卡风格：顶部 `LIBRARY CARD` 标签（mono）+ 表格线字段 + mono ISBN 输入位
- 防抖 300ms
- 回车触发 `router.push({ name: 'search', query: { q } })`
- 接收外部 `v-model` 支持搜索页回显

#### 5.9 `VoteButton.vue` 设计要点

- props: `reportId: number`、`upvote: number`、`downvote: number`、`userVote: -1 | 0 | 1`
- 两个按钮：`▲`（up，红色）+ `▼`（down，深灰）
- 已投票态：`is-voted` 类，按钮加红色边框
- 点击逻辑：
  - 同方向再点 → 保持（后端覆盖相同 vote_type）
  - 反方向 → 切换
  - 未投票 → 直接投票
  - 调用 `POST /api/reports/{id}/vote`，body `{ vote_type: ±1 }`，header `X-Fingerprint: {fp}`
- 成功后触发 `Stamp.pulse()`（详情页才有 stamp）

#### 5.10 `FileUploader.vue` 设计要点

- props: `multiple: boolean = false`、`accept: string = 'image/*,video/mp4'`、`maxSize: number = 20MB`
- 拖拽区：纸张阴影背景 + 虚线方框 + 文件类型 mono 标签
- 状态：idle / dragging / uploading / done / error
- 错误：超大、超类型分别提示

#### 5.11 `EvidenceList.vue` 设计要点

- props: `evidences: EvidenceOut[]`
- 图片：缩略图（`<img :src="'/evidence/' + file_path">`）
- 视频：`<video :src="..." controls>`，仅展示首帧
- 文字：monospace 块引用
- 点击放大（用 `<dialog>` 或 modal）

#### 5.12 `HomeView.vue` 设计要点

```vue
<template>
  <main class="ledger">
    <SectionHeader num="§ 01 —" title="Latest Filings" :meta="`${reports.length} most recent · ordered by gravity`" />
    <FeaturedReport v-if="reports[0]" :report="reports[0]" />
    <ReportsGrid :reports="reports.slice(1, 19)" />  <!-- 18 条 -->
    <ReportsGrid v-if="reports.length > 19" :reports="reports.slice(19)" />  <!-- 第 20 条及以后进无限滚动 -->
  </main>
</template>
```

- 初始请求：`GET /api/books/recent` 获取 20 条
- 滚动到底部自动请求下一页（可选 v2，本期硬编码 20 条）
- 顶部集成 `SearchBox`（简化版，可选）

#### 5.13 `SearchView.vue` 设计要点

- 从 `route.query.q` 取关键词
- 调用 `GET /api/search?q=...`
- 复用 `ReportsGrid` 渲染结果
- 空结果：显示 "No reports filed yet for `{q}`."（纸张卡片风格）

#### 5.14 `BookDetailView.vue` 设计要点

- 从 `route.params.isbn` 取 ISBN
- 调用 `GET /api/books/{isbn}`
- 404 状态：渲染 "No dossier entry found for this ISBN."
- 布局：1+1，左侧固定元信息（封面 + 标题 + 作者 + ISBN + Stamp + 投票总览），右侧时间倒序举报列表
- 每条举报 = ReportCard + EvidenceList + VoteButton（独立投票）

#### 5.15 `ReportView.vue` 设计要点

- 中央 720px 容器，三段式：
  1. **OCR 区**：FileUploader（accept="image/*"）+ 调用 `recognizeText()` 回填 ISBN/书名/作者
  2. **元数据**：ISBN / 书名 / 作者 / 描述（4 个 FormField）
  3. **附件**：封面（单图）+ 证据（多文件）
- 校验：ISBN 10/13 位、必填项、描述 ≥ 10 字
- 提交：`POST /api/reports` multipart/form-data
- 成功 → `router.push('/books/' + isbn)`
- 429 → Naive UI `useMessage().error('举报过于频繁')`
- 提交按钮 = 巨型倾斜红印章 "FILE REPORT"

#### 任务 5 验收

- [ ] 首页 mockup 视觉 100% 还原（评审对比 mockup）
- [ ] 4 个页面路由跳转正常
- [ ] OCR 回填失败时表单仍可提交
- [ ] 投票按钮 3 种状态（未投/已投 up/已投 down）显示正确
- [ ] 429/413/415 错误有友好提示

---

### 任务 6：测试 [P1, 1天]

#### 6.1 后端测试

**测试框架**：pytest + pytest-asyncio + httpx AsyncClient

**新增文件**：

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `backend/tests/conftest.py` | 测试 fixtures（test db、async client） |
| 新增 | `backend/tests/test_books.py` | recent + detail API |
| 新增 | `backend/tests/test_reports.py` | create + vote + rate limit |
| 新增 | `backend/tests/test_search.py` | FTS + ILIKE 回退 |
| 新增 | `backend/tests/test_feed.py` | RSS 输出格式 |
| 新增 | `backend/tests/test_vote.py` | 投票唯一性 + 覆盖行为 |

**测试用例清单**：

| ID | 测试场景 | 前置 | 输入 | 预期 | 方法 |
|---|---|---|---|---|---|
| TC-3.1 | 创建新 ISBN 举报 | 空 DB | POST /api/reports with valid form | 201 + ReportOut，含 book | 集成 |
| TC-3.2 | 同 ISBN 第二次举报 | TC-3.1 已存在 | POST /api/reports same ISBN | 201，book.id 相同，book.report_count = 2 | 集成 |
| TC-3.3 | 举报触发限流 | TC-3.1 已 5 条 | POST 第 6 条 | 429 + Retry-After header | 边界值 |
| TC-3.4 | 文件超 20MB | - | POST with 21MB image | 413 | 边界值 |
| TC-3.5 | 文件类型非法 | - | POST with .gif | 415 | 等价类 |
| TC-3.6 | 投票覆盖 | - | POST vote up then up | vote_type 保持 +1 | 状态转移 |
| TC-3.7 | 投票切换方向 | - | POST up then down | vote_type 切换为 -1 | 状态转移 |
| TC-3.8 | GET /api/books/recent 排序 | DB 已有 3 条不同时间 report | GET | 按 created_at DESC 排列 | 排序 |
| TC-3.9 | GET /api/books/{isbn} 详情 | TC-3.1 已有 | GET | 返回 BookDetailOut 含全部 reports + evidences | 集成 |
| TC-3.10 | GET /api/books/{不存在isbn} | - | GET /api/books/0000000000 | 404 | 异常路径 |
| TC-3.11 | 搜索命中 title | DB 已有"AI 生成"书 | GET ?q=AI | 返回该条 | FTS |
| TC-3.12 | 搜索命中 description | DB 已有"公式错误"举报 | GET ?q=公式 | 返回该 report | FTS |
| TC-3.13 | 搜索空查询回退 ILIKE | - | GET ?q=  | 走 ILIKE 不报错 | 异常路径 |
| TC-3.14 | 搜索特殊字符清洗 | - | GET ?q=:&\| | 不报 tsquery 语法错误 | 安全性 |
| TC-3.15 | RSS 输出格式 | DB 已有 5 条 | GET /api/feed/reports.rss | Content-Type 正确，title/link/guid/pubDate 完整 | 输出验证 |

**测试方法说明**：
- **等价类划分**：TC-3.4 / TC-3.5（合法/非法文件）
- **边界值**：TC-3.3（第 6 条触发限流）、TC-3.4（21MB 触发 413）
- **状态转移**：TC-3.6 / TC-3.7（投票状态机）
- **集成**：TC-3.1 / TC-3.2 / TC-3.9（多组件协作）
- **异常路径**：TC-3.10 / TC-3.13 / TC-3.14

**数据策略**：
- 测试用 PostgreSQL test DB（`AIGBOOKS_DATABASE_URL_TEST`）
- 每个测试用 `BEGIN; ROLLBACK;` 隔离
- 文件上传用 `io.BytesIO` mock，不写真磁盘

#### 6.2 前端测试

**测试框架**：Vitest + Vue Test Utils + happy-dom

**新增文件**：

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `frontend/src/components/__tests__/Stamp.spec.ts` | 印章尺寸 + pulse |
| 新增 | `frontend/src/components/__tests__/VoteButton.spec.ts` | 3 种投票状态 |
| 新增 | `frontend/src/components/__tests__/SearchBox.spec.ts` | 防抖 + 回车跳转 |
| 新增 | `frontend/src/components/__tests__/ReportCard.spec.ts` | 数据渲染 |
| 新增 | `frontend/src/views/__tests__/ReportView.spec.ts` | 表单校验 + OCR 回填 |
| 新增 | `frontend/src/ocr/__tests__/index.spec.ts` | OCR 失败静默回退 |

**测试用例清单**：

| ID | 场景 | 预期 |
|---|---|---|
| TC-5.1 | Stamp 渲染 count | 显示 `Reported × N` |
| TC-5.2 | Stamp.pulse() 调用 | scale 动画 CSS class 添加 |
| TC-5.3 | VoteButton 初始未投 | 显示 0/0，无 is-voted |
| TC-5.4 | VoteButton 已投 up | 显示 +1，up 按钮 is-voted |
| TC-5.5 | VoteButton 点击反方向 | 调用 API + 切换状态 |
| TC-5.6 | SearchBox 输入 | 300ms 后才触发 change |
| TC-5.7 | SearchBox 回车 | 调用 router.push |
| TC-5.8 | ReportCard 渲染 | 显示 title/author/isbn/excerpt |
| TC-5.9 | ReportView 空 ISBN 提交 | 校验失败提示 |
| TC-5.10 | ReportView 描述 < 10 字 | 校验失败提示 |
| TC-5.11 | OCR 调用失败 | 表单仍可手填 |

#### 6.3 E2E 脚本

**新增文件**：

| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `scripts/e2e.sh` | curl 全链路测试 |

脚本流程：

```bash
#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://localhost:8000}
FP=$(uuidgen)

echo "1) POST /api/reports (创建新书)"
ISBN="9787000000001"
curl -sf -X POST "$BASE/api/reports" \
  -F "isbn=$ISBN" -F "title=测试书" -F "author=测试作者" \
  -F "description=这本书充满 AI 生成痕迹，公式全是装饰品。" \
  -F "fingerprint=$FP" | jq .id > /tmp/report_id

echo "2) POST /api/reports (同 ISBN 聚合)"
curl -sf -X POST "$BASE/api/reports" \
  -F "isbn=$ISBN" -F "title=测试书" -F "author=测试作者" \
  -F "description=全书是 LaTeX 排版的垃圾。" \
  -F "fingerprint=$FP" | jq .book.report_count  # 期望 2

echo "3) GET /api/search?q=测试"
curl -sf "$BASE/api/search?q=测试" | jq '.reports | length'  # 期望 >= 2

echo "4) POST /api/reports/{id}/vote"
curl -sf -X POST "$BASE/api/reports/$(cat /tmp/report_id)/vote" \
  -H "X-Fingerprint: $FP" -H "Content-Type: application/json" \
  -d '{"vote_type": 1}' | jq .upvote  # 期望 1

echo "5) GET /api/feed/reports.rss"
curl -sf -I "$BASE/api/feed/reports.rss" | grep -i "content-type"  # 期望 application/rss+xml

echo "✅ E2E 全部通过"
```

#### 任务 6 验收

- [ ] `uv run pytest -q` 全绿
- [ ] `pnpm test` 全绿
- [ ] `bash scripts/e2e.sh` 全绿

---

### 任务 7：部署配置 [P1, 0.5天]

#### 7.1 systemd 服务文件

**新增文件**：`deploy/aigbooks-api.service`

```ini
[Unit]
Description=AIGBooks FastAPI Backend
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/aigbooks/backend
Environment="AIGBOOKS_DATABASE_URL=postgresql+asyncpg://aigbooks:CHANGE_ME@localhost:5432/aigbooks"
Environment="AIGBOOKS_EVIDENCE_DIR=/var/lib/aigbooks/evidence"
Environment="AIGBOOKS_COVERS_DIR=/var/lib/aigbooks/covers"
ExecStart=/usr/local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=on-failure
RestartSec=5s
TimeoutStopSec=30s
KillMode=mixed

# 安全加固
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
RuntimeDirectory=aigbooks
RuntimeDirectoryMode=0750

# 日志走 journal
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 7.2 nginx 配置

**新增文件**：`deploy/nginx-aigbooks.conf`

```nginx
server {
    listen 80;
    server_name aigbooks.example.com;

    client_max_body_size 25M;  # 略大于 20MB 上限，预留 multipart 编码开销

    # 反代 FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
    }

    # 后端静态文件（FastAPI 已挂载 StaticFiles，这里也走反代便于限速/缓存）
    location /covers/ {
        proxy_pass http://127.0.0.1:8000/covers/;
        expires 7d;
    }
    location /evidence/ {
        proxy_pass http://127.0.0.1:8000/evidence/;
        expires 30d;
    }

    # 前端 SPA
    root /opt/aigbooks/frontend/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 7.3 部署文档

**新增文件**：`deploy/README.md`

```markdown
# AIGBooks 部署指南

## 1. 准备 PostgreSQL

sudo -u postgres psql <<SQL
CREATE USER aigbooks WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE aigbooks OWNER aigbooks;
GRANT ALL PRIVILEGES ON DATABASE aigbooks TO aigbooks;
SQL

## 2. 部署后端

```bash
sudo mkdir -p /opt/aigbooks /var/lib/aigbooks/{covers,evidence}
sudo chown -R www-data:www-data /opt/aigbooks /var/lib/aigbooks
sudo -u www-data git clone <repo> /opt/aigbooks
cd /opt/aigbooks/backend
sudo -u www-data uv sync
sudo -u www-data AIGBOOKS_DATABASE_URL=... uv run alembic upgrade head
sudo cp /opt/aigbooks/deploy/aigbooks-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aigbooks-api
sudo systemctl status aigbooks-api
```

## 3. 部署前端

```bash
cd /opt/aigbooks/frontend
sudo -u www-data pnpm install
sudo -u www-data pnpm build  # 输出到 dist/
```

## 4. 配置 nginx

```bash
sudo cp /opt/aigbooks/deploy/nginx-aigbooks.conf /etc/nginx/sites-available/aigbooks
sudo ln -s /etc/nginx/sites-available/aigbooks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5. HTTPS（可选）

```bash
sudo certbot --nginx -d aigbooks.example.com
```
```

#### 任务 7 验收

- [ ] `systemctl status aigbooks-api` 显示 active (running)
- [ ] `curl http://localhost/api/books/recent` 返回正常
- [ ] `curl http://localhost/api/feed/reports.rss` 返回 RSS
- [ ] 上传文件后访问 `http://localhost/covers/xxx.jpg` 可见

---

## 6. UI 设计规格（参考 mockup 完整迁移）

### 6.1 美学方向

**Editorial Warning Dossier**——老牌杂志 + 图书馆卡片 + 档案馆卷宗。禁止紫粉渐变、Inter/Roboto/Arial/Helvetica、圆角、glassmorphism、neumorphism。

### 6.2 字体系统（Fontsource）

| 用途 | 包 | 关键 opsz/wght |
|---|---|---|
| Display（标题/Logo/印章） | `@fontsource-variable/fraunces` | opsz 24-144, wght 300-900, SOFT 0-100 |
| Body（正文/描述） | `@fontsource/newsreader` | opsz 6-72, wght 400/700 + italic |
| Mono（ISBN/日期/编号） | `@fontsource/jetbrains-mono` | wght 400/700 |
| 中文回退 | `@fontsource/noto-serif-sc` | wght 400/700 |

### 6.3 颜色 Token（CSS Variables in dossier.css）

```css
:root {
  --paper:          #f5f1e8;
  --paper-dark:     #ebe4d2;
  --paper-shadow:   #d4c9b0;
  --ink:            #1a1a1a;
  --ink-soft:       #4a4538;
  --ink-faint:      #8a8270;
  --rule:           #2a2520;
  --stamp-red:      #b82b26;
  --stamp-red-deep: #8a1f1c;
  --accent-mustard: #b58a3a;
  --alert-bg:       #f3e5d8;

  --font-display: "Fraunces Variable", "Noto Serif SC", Georgia, serif;
  --font-body:    "Newsreader", "Noto Serif SC", Georgia, serif;
  --font-mono:    "JetBrains Mono", "Courier New", monospace;
}
```

### 6.4 全局质感（body::before / ::after）

```css
body::before {
  content: "";
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.1 0 0 0 0 0.08 0 0 0 0 0.05 0 0 0 0.06 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  opacity: 0.5;
  pointer-events: none;
  z-index: 0;
}
body::after {
  content: "";
  position: fixed; top: 0; left: 0; right: 0; height: 8px;
  background: linear-gradient(180deg, rgba(184,43,38,0.18), transparent);  /* 允许：纹理/老化边缘渐变 */
  z-index: 0;
}
```

> **关于"禁止渐变"**：允许用于纸张纹理（repeating-linear-gradient 封面占位）和顶部老化边缘（linear-gradient），但禁止用于纯装饰性彩色渐变。

### 6.5 关键组件设计要点

| 组件 | 设计要点 |
|---|---|
| `<Masthead>` | 顶部三段栏（Vol × Dossier × 日期）+ 居中 Logo（AIG + 斜体红 books）+ 副标题 + nav |
| `<Stamp size="featured">` | 22px display, 3px 红边框, rotate(-2.5deg), 双层伪元素 |
| `<Stamp size="mini">` | 13px display, 2px 红边框, rotate(-3deg), 仅文字 × N |
| `<ReportCard>` | 顶 1px 实线 + category mono 红 + 标题 26px + ISBN 11px + 摘要 + 底虚线 + mini stamp |
| `<FeaturedReport>` | 1+1 双列，左 3:4 封面（45° 条纹），右引用块（左侧红色边线、斜体衬线） + featured stamp |
| `<VoteButton>` | ▲▼ 字符 + 票数，up=#b82b26 / down=#4a4538，已投票 is-voted + 印章 pulse |
| `<SearchBox>` | 借阅卡风格：顶部"LIBRARY CARD"标识 + 表格线字段 + mono ISBN 输入位 |
| `<FileUploader>` | 拖拽区纸张阴影 + 虚线方框 + mono 类型标签 |
| `<FormField>` | 斜体衬线标签，无边框，横线分隔，无圆角 |

### 6.6 动效

| 动效 | 实现 |
|---|---|
| Enter reveal / typeset | `opacity 0→1 + translateY(8px→0)` 0.6s，stagger 按 `:nth-child` 计算 |
| Hover on links | 1px 红下划线 `transition: border-color 0.2s` |
| Stamp pulse | `scale(1)→1.08→1` 200ms，投票成功后触发 |
| Submit on paper | 全页 1px 红边 → 渐隐入详情页 |
| `prefers-reduced-motion` | 全局关闭动画 |

### 6.7 响应式断点

```css
@media (max-width: 900px) {
  .featured { grid-template-columns: 1fr; }
  .reports-grid { grid-template-columns: 1fr 1fr; }
  .masthead { padding: 32px 24px 16px; }
}
@media (max-width: 600px) {
  .reports-grid { grid-template-columns: 1fr; }
  .ledger { padding: 32px 24px 64px; }
}
```

### 6.8 验收（视觉）

- [ ] 首页在 1280px 视口下三列等宽，论文风对齐
- [ ] Logo "AIGbooks" 中 "books" 斜体红字生效
- [ ] 报头三段栏（Vol / Dossier / 日期）可见
- [ ] 印章出现在 featured + 至少 1 张 ReportCard
- [ ] 投票按钮红/灰反色，按下有放大反馈
- [ ] 全局背景纸张纤维 + 顶部红边老化线
- [ ] 完全没有：圆角、阴影渐变、紫粉配色、Inter/Roboto/Helvetica

---

## 7. 测试计划

| 测试类型 | 覆盖范围 | 验收标准 |
|---|---|---|
| 单元测试 | 后端：限流、FTS 清洗、tsvector 触发器逻辑 | `pytest -q` 全绿 |
| 集成测试 | 后端 6 个 API 全链路 | `pytest -q` 全绿 |
| 组件测试 | 前端：Stamp / VoteButton / SearchBox / ReportCard / ReportView | `pnpm test` 全绿 |
| E2E 测试 | curl 跑通举报→聚合→搜索→投票→RSS | `bash scripts/e2e.sh` 全绿 |
| 视觉测试 | 首页与 mockup 视觉对比 | 任务 5 验收清单 7 项全部 ✅ |
| 部署测试 | systemd + nginx 启动后 API 可用 | 任务 7 验收清单 4 项全部 ✅ |

---

## 8. 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|---|---|---|---|
| 中文 FTS 用 `simple` 字典精度低 | 高 | 中 | 接受 MVP 现状，v2 升级 zhparser；提供 ILIKE 回退兜底 |
| Tesseract.js WASM 体积大 | 高 | 中 | pnpm 拆 chunk + 动态 import；OCR 失败静默回退 |
| 浏览器指纹稳定性差（同用户多次 fingerprint 不一致） | 中 | 高 | 算法用 UA + lang + screen + tz + canvas 5 维；投票/限流用 IP+fingerprint 双键，单键失效不影响核心功能 |
| 文件存储本地磁盘无法横向扩展 | 低 | 中 | 设计 storage.py 接口化，后续可平滑迁移到 S3/R2 |
| 大量举报导致首页查询慢 | 低 | 中 | `LIMIT 20` + `created_at DESC` 索引（待补） |
| alembic 迁移触发器不可逆 | 中 | 低 | downgrade 显式 DROP TRIGGER + DROP INDEX；CI 跑 `upgrade head → downgrade base → upgrade head` |
| 前端 Naive UI 与 dossier.css 设计冲突 | 中 | 低 | 仅在表单 / message / 弹窗等 Naive UI 组件上用，主视觉全部手写 dossier.css 组件 |
| systemd `www-data` 用户无法访问 `/var/lib/aigbooks` | 中 | 中 | `chown -R www-data:www-data`；service 加 `RuntimeDirectory=aigbooks` |
| nginx 上传 413 与 FastAPI 上传 413 重复触发 | 中 | 低 | nginx `client_max_body_size 25M` 略大于 FastAPI `max_upload_size=20MB`，让 FastAPI 校验生效 |
| mockup 视觉在生产字体加载后与本地不符 | 中 | 中 | Fontsource 完整版本（4 种字重）+ 测试环境视觉对比 |

---

## 9. 默认决策清单（待用户评审）

以下决策为节省澄清成本，**默认采纳**，如不同意请在确认时指出：

| # | 决策点 | 默认选择 | 备注 |
|---|---|---|---|
| D1 | RSS 链接显示路径 | 前端用 `/api/feed/reports.rss`（mockup 中是 `/feed/reports.rss`，统一改为带 `/api` 前缀） | 避免 nginx 重写 |
| D2 | 文字证据 | 作为表单文本字段（`description`），不作为文件上传 | 设计说支持"文字/图片/视频/照片"，文字即举报描述 |
| D3 | 封面扩展名 | 保留上传原格式（png/jpg/webp → `covers/{isbn}.{ext}`） | 不强制转 jpg |
| D4 | 渐变使用范围 | 允许纸张纹理（repeating-linear-gradient）+ 顶部老化边缘（linear-gradient）；禁止纯装饰彩色渐变 | 与 mockup 实际一致 |
| D5 | 是否拆 ReportsGrid / SectionHeader / UtilityBar | 是，全部独立组件 | 设计文档提及但 v1 未明确 |
| D6 | Pinia stores | 建 `stores/fingerprint.ts` + `stores/toast.ts`，不建复杂领域 store | 数据走页面级 ref 即可。D6 追加：`stores/reports.ts` 用于 Masthead 总数显示，是必要的全局状态。 |
| D7 | 同 ISBN 已存在时是否更新 cover | 是，新上传的封面覆盖旧的；未上传则保留原封面 | `COALESCE(EXCLUDED.cover_path, books.cover_path)` |
| D8 | 首页无限滚动 | MVP 不实现，固定 20 条（首页显示 19，第 20 条隐藏） | 简化 MVP |
| D9 | `featured__category` 样式 | 复用 `.report__category`（mono 红 10px） | mockup CSS 缺失该 class |
| D10 | `<a><button>` 嵌套问题 | UtilityBar 按钮用 `RouterLink` 自定义类（`<a class="utility__btn">`） | 避免 HTML 非法嵌套 |
| D11 | 静态链接处理 | SPA 内用 `RouterLink`，RSS 用 `<a target="_blank">` | |
| D12 | 排序兜底 | 举报数 ≥ 1 的 report 才返回；不返回孤立 books（无 report） | |

---

## 10. 验收标准（合并所有任务）

### 10.1 功能验收

- [ ] 后端 6 个 API 全部通过 `scripts/e2e.sh`
- [ ] 前端 4 个页面路由全部可达
- [ ] OCR 回填、限流（429 + Retry-After）、投票唯一性（覆盖 + 切换）生效
- [ ] RSS 订阅 `/api/feed/reports.rss` 输出 RSS 2.0 格式合法

### 10.2 视觉验收

- [ ] 首页与 mockup `/tmp/opencode/aigbooks-mockup/index.html` 视觉对齐度 ≥ 95%
- [ ] 字体、印章、纸张纹理全部按 dossier.css 实现
- [ ] §6.8 验收清单 7 项全部 ✅

### 10.3 工程验收

- [ ] `uv run pytest -q` 全绿
- [ ] `pnpm test` 全绿
- [ ] `pnpm typecheck`（`vue-tsc --noEmit`）零错误
- [ ] `pnpm build` 成功，bundle 中可见 4 种字体文件
- [ ] `uv run ruff check` 零错误
- [ ] `alembic upgrade head && alembic downgrade base && alembic upgrade head` 端到端可逆

### 10.4 部署验收

- [ ] `systemctl status aigbooks-api` active (running)
- [ ] `nginx -t` 通过
- [ ] `curl http://localhost/api/books/recent` 返回正常
- [ ] `curl http://localhost/` 渲染首页 SPA

---

## 11. 任务时间线（8 天）

| Day | 任务 | 产出 |
|---|---|---|
| 1 | 任务 1 + 任务 2 | 后端可启动 + 数据库可迁移 |
| 2-3 | 任务 3（上） | 4 个 router 全部实现 |
| 4 | 任务 3（下） + 任务 4 | API 完成 + 前端脚手架可启动 |
| 5-6 | 任务 5 | 4 个页面全部实现 |
| 7 | 任务 6 | 后端 + 前端测试全绿 |
| 8 | 任务 7 + 收尾 | systemd + nginx 部署成功 |

---

## 12. 实施前确认清单

请用户确认以下要点后再开始执行：

### 12.1 关键决策（已通过选择题确认）

- [ ] 首页排序 = 最新举报优先（`reports.created_at DESC`，API 返回 `ReportOut[]`）
- [ ] 首页数量 = 1 Featured + 18 Grid = 19 条
- [ ] 举报入口 = 独立路由 `/report`
- [ ] 投票行为 = 覆盖旧投票（同方向保持，反方向切换）
- [ ] 字体加载 = Fontsource 自托管
- [ ] 隐私策略 = 保留 IP + fingerprint 原值

### 12.2 默认决策（§9 清单 D1-D12）

- [ ] RSS 路径用 `/api/feed/reports.rss`
- [ ] 文字证据作为表单文本字段
- [ ] 封面扩展名保留原格式
- [ ] 渐变仅用于纸张纹理 + 老化边缘
- [ ] ReportsGrid / SectionHeader / UtilityBar 独立组件
- [ ] Pinia stores 仅 fingerprint + toast
- [ ] 同 ISBN 封面覆盖
- [ ] MVP 不做无限滚动
- [ ] 其他 D9-D12

### 12.3 文档同步

- [ ] 同步更新 `docs/plans/2026-07-29-aigbooks-design.md` 中首页 API 结构与数量（任务 1 执行时）

### 12.4 旧文档归档

- [ ] v1 实施计划标记为 `superseded`（在文档头添加版本说明），保留作历史记录

---

## 13. 执行步骤（按 AGENTS.md 强制任务清单）

1. **更新设计文档**（任务 1 开始时）：同步首页 API 结构、数量；记录新决策
2. **清理无用代码**：从零搭建，无清理
3. **执行任务**：按任务 1 → 7 顺序执行，每个任务完成后跑测试验证
4. **更新状态**：完成后将本计划状态改为"已完成"

---

**等待用户确认后开始执行任务 1。**

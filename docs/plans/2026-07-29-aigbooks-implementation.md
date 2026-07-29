# AIGBooks 实施计划

---
创建时间: 2026-07-29 17:20
状态: 待确认
---

## 1. 计划概述

| 维度 | 内容 |
|---|---|
| 目标 | 从零搭建 AIGBooks AI 生成书黑名单网站，实现匿名举报、浏览、搜索、投票、RSS 全流程 |
| 范围 | 后端 6 个 API + 前端 4 个页面 + 数据库 4 张表 + 部署配置 |
| 预期成果 | 单服务器可运行的完整 Web 应用 |
| 优先级 | MVP 全部必做 |

## 2. 背景

AI 生成劣质书籍泛滥，读者缺乏甄别渠道。AIGBooks 通过自由举报 + 匿名浏览 + 按 ISBN 聚合，让读者快速避坑。无账号，零审核。

## 3. 影响范围

| 层级 | 影响 |
|---|---|
| 后端 | 全部新建：FastAPI 入口、路由、模型、中间件、FTS 查询、文件上传、RSS 生成 |
| 数据库 | 全部新建：4 张表 + GIN 索引 + tsvector 触发器 + Alembic 迁移 |
| 前端 | 全部新建：Vue 3 项目、路由、状态、API 层、OCR 封装、4 个页面 |
| 部署 | 全部新建：systemd 服务、nginx 配置 |

## 4. 任务分解

### 任务 1：后端项目脚手架 [P0, 0.5天]
- 1.1 创建 pyproject.toml + uv 依赖 [0.1天]
- 1.2 创建 main.py（FastAPI 入口） [0.1天]
- 1.3 创建 config.py（pydantic-settings） [0.1天]
- 1.4 创建 database.py（异步引擎 + session） [0.1天]
- 1.5 初始化 Alembic [0.1天]

### 任务 2：数据模型与迁移 [P0, 1天]
- 2.1 创建 models.py（Book, Report, Evidence, Vote 四表 ORM） [0.3天]
- 2.2 创建 schemas.py（Pydantic 请求/响应模型） [0.2天]
- 2.3 编写 Alembic 迁移（建表 + FTS 触发器 + GIN 索引） [0.3天]
- 2.4 验证迁移可执行 [0.2天]

### 任务 3：后端 API 实现 [P0, 2天]
- 3.1 创建 routers/books.py（GET recent + GET detail） [0.3天]
- 3.2 创建 routers/reports.py（POST create + POST vote） [0.4天]
- 3.3 创建 routers/search.py（PG FTS 全文检索） [0.3天]
- 3.4 创建 routers/feed.py（RSS 2.0 生成） [0.2天]
- 3.5 创建 search.py（FTS 查询封装 + 输入清洗） [0.2天]
- 3.6 创建 middleware/rate_limit.py（举报限流） [0.2天]
- 3.7 创建 middleware/exception.py（全局异常处理） [0.2天]
- 3.8 文件上传服务（存储路径 + MIME 校验 + 大小限制） [0.2天]

### 任务 4：前端项目脚手架 [P0, 0.5天]
- 4.1 创建 Vue 3 + Vite + TypeScript 项目 [0.1天]
- 4.2 安装 Naive UI + Vue Router + Pinia [0.1天]
- 4.3 创建 api/ 封装层（axios + 拦截器） [0.15天]
- 4.4 创建 ocr/ 封装（Tesseract.js） [0.15天]

### 任务 5：前端页面实现 [P0, 2.5天]
- 5.1 首页（最新 20 条举报卡片列表） [0.5天]
- 5.2 搜索页（搜索结果列表 + 高亮） [0.5天]
- 5.3 书籍详情页（ISBN 聚合 + 举报列表 + 证据 + 投票） [0.6天]
- 5.4 举报表单（多文件上传 + OCR 回填 + 校验） [0.6天]
- 5.5 公共组件（举报卡片、搜索框、文件上传、投票按钮） [0.3天]

### 任务 6：测试 [P1, 1天]
- 6.1 后端 API 测试（pytest + httpx） [0.4天]
- 6.2 前端组件测试（Vitest + Vue Test Utils） [0.3天]
- 6.3 E2E curl 脚本 [0.3天]

### 任务 7：部署配置 [P1, 0.5天]
- 7.1 systemd 服务文件 [0.1天]
- 7.2 nginx 配置 [0.2天]
- 7.3 部署文档 [0.2天]

**总计：P0 6.5天 + P1 1.5天 = 8天**
## 5. 任务详情

### 5.1 任务 1：后端项目脚手架

**新增文件：** backend/pyproject.toml, backend/app/__init__.py, backend/app/main.py, backend/app/config.py, backend/app/database.py, backend/alembic.ini, backend/alembic/env.py, backend/alembic/script.py.mako

**config.py 设计要点：** 使用 pydantic_settings.BaseSettings，环境变量前缀 AIGBOOKS_，支持 .env。关键字段：database_url(postgresql+asyncpg://), evidence_dir, covers_dir, max_upload_size(20MB), allowed_mime_types(image/jpeg|image/png|image/webp|video/mp4), report_rate_limit(5), report_rate_window(3600), page_size(20)

**main.py 设计要点：** 创建 FastAPI 实例，挂载 StaticFiles(evidence/covers)，注册 4 个 router: books, reports, search, feed

**pyproject.toml 依赖：** fastapi>=0.115, uvicorn[standard]>=0.32, sqlalchemy[asyncio]>=2.0, asyncpg>=0.30, alembic>=1.14, pydantic>=2.9, pydantic-settings>=2.5, python-multipart>=0.0.12, feedgen>=1.0。dev: pytest>=8, pytest-asyncio>=0.24, httpx>=0.27

### 5.2 任务 2：数据模型与迁移

**新增文件：** backend/app/models.py, backend/app/schemas.py, backend/alembic/versions/001_init.py

**ORM 模型设计：** Book(isbn TEXT UNIQUE, title, author, cover_path, report_count INT, tsv_meta TSVECTOR, created_at, updated_at)。Report(book_id FK CASCADE, description, tsv_desc TSVECTOR, upvote, downvote, ip INET, fingerprint, created_at)。Evidence(report_id FK CASCADE, file_path, file_kind, mime_type, size_bytes, created_at)。Vote(report_id FK CASCADE, ip INET, fingerprint, vote_type SMALLINT, created_at, UNIQUE(report_id, ip, fingerprint))。全部使用 mapped_column + BigInteger 主键，server_default=func.now() 时间戳。不定义 relationship（YAGNI，显式 join 查询）

**迁移 SQL 要点（3 个触发器 + 3 个 GIN 索引）：** 1. books_tsv_meta_trigger: BEFORE INSERT OR UPDATE, setweight(to_tsvector(simple, title), A) || setweight(to_tsvector(simple, author), B) -> NEW.tsv_meta。2. reports_tsv_desc_trigger: BEFORE INSERT OR UPDATE, to_tsvector(simple, description) -> NEW.tsv_desc。3. update_book_report_count: AFTER INSERT OR DELETE ON reports, books.report_count +/- 1。4. GIN 索引: books_tsv_meta_idx, reports_tsv_desc_idx, reports_rate_limit_idx(ip, fingerprint, created_at)

**Pydantic Schema 设计：** ReportCreate(isbn 10-17, title 1-500, author 1-200, description 1-5000, ip, fingerprint)。VoteCreate(vote_type -1|1, ip, fingerprint)。BookOut(isbn, title, author, cover_path, report_count, created_at, updated_at, reports list[ReportOut])。ReportOut(id, book_id, description, upvote, downvote, created_at, evidences list[EvidenceOut])。EvidenceOut(id, file_path, file_kind, mime_type, size_bytes, created_at)。SearchResult(books list[BookOut], total int)

### 5.3 任务 3：后端 API 实现

**3.1 routers/books.py — GET /api/books/recent, GET /api/books/{isbn}：** recent: 按 books.report_count DESC, books.updated_at DESC 取 page_size 条，join reports + evidences。detail: 按 isbn 查 book，join 全部 reports + evidences，按 created_at DESC；不存在返回 404

**3.2 routers/reports.py — POST /api/reports, POST /api/reports/{id}/vote：** create 流程: 1.校验文件 MIME 类型+大小 2.限流检查 SELECT count(*) FROM reports WHERE ip=? AND fingerprint=? AND created_at >= NOW() - interval 1 hour, >=5 返回 429 3.保存封面到 covers/{isbn}.jpg, 证据到 evidence/{yyyy}/{mm}/{uuid}.{ext} 4.事务: INSERT INTO books ... ON CONFLICT (isbn) DO NOTHING RETURNING id -> INSERT INTO reports -> INSERT INTO evidences(批量) 5.返回新建的 report(含 book)。vote 流程: 1.INSERT INTO votes ... ON CONFLICT (report_id, ip, fingerprint) DO UPDATE SET vote_type=EXCLUDED.vote_type 2.更新 reports.upvote/downvote 计数

**3.3 routers/search.py — GET /api/search?q=：** CTE + UNION 查询策略。参数化查询防 SQL 注入。输入清洗 re.sub(r[:&|!()*], ' ', query).strip()。若清洗后为空回退 ILIKE 模糊匹配

**3.4 routers/feed.py — GET /api/feed/reports.rss：** 使用 feedgen.feed.RssGenerator。item: title=[{isbn}] {title} - {author}, link=https://{host}/books/{isbn}, guid=report-{id}, description=CDATA(reports.description)。Response: Response(content=rss_str, media_type=application/rss+xml)

**3.5 search.py — FTS 查询封装：** 导出 search_books(db, query: str, page_size: int) -> list[Book]。输入清洗+参数化查询+回退 ILIKE

**3.6 middleware/rate_limit.py：** 从 request.client.host 或 X-Forwarded-For 取 IP。从 X-Fingerprint header 取指纹。仅在 POST /api/reports 路由生效。超过阈值返回 HTTPException(429, {code: 429, msg: 举报过于频繁，请稍后再试})

**3.7 middleware/exception.py：** 全局 @app.exception_handler(Exception) 捕获未处理异常。返回 {code: 500, msg: 服务器内部错误}，日志记录 traceback。HTTPException 保留原 status_code + detail

**3.8 文件上传服务：** save_cover(file, isbn) -> str | None: 写入 covers/{isbn}.jpg。save_evidence(file) -> str: 写入 evidence/{yyyy}/{mm}/{uuid}.{ext}。校验: MIME 白名单, 文件大小 <= 20MB。返回相对路径

### 5.4 任务 4：前端项目脚手架

**新增文件：** frontend/package.json, frontend/vite.config.ts, frontend/tsconfig.json, frontend/src/main.ts, frontend/src/App.vue, frontend/src/router/index.ts, frontend/src/api/index.ts, frontend/src/api/books.ts, frontend/src/api/reports.ts, frontend/src/api/search.ts, frontend/src/ocr/index.ts

**技术要点：** vite.config.ts: server.proxy 将 /api, /evidence, /covers 代理到 http://localhost:8000。api/index.ts: axios 实例，baseURL=/api，拦截器统一错误提示（Naive UI message）。ocr/index.ts: recognizeText(image: File): Promise<{isbn?: string, title?: string, author?: string}>，失败静默回退

**路由定义：** / -> HomeView(首页最新20条), /search?q= -> SearchView(搜索结果), /books/:isbn -> BookDetailView(书籍详情), /report -> ReportView(举报表单)

### 5.5 任务 5：前端页面实现

**5.1 首页（HomeView）：** 调用 GET /api/books/recent，渲染 ReportCard 组件列表。顶部搜索框，输入后跳转 /search?q=xxx。底部 RSS 链接 /api/feed/reports.rss。我要举报按钮，跳转 /report

**5.2 搜索页（SearchView）：** 从 URL 读取 ?q= 参数，调用 GET /api/search?q=xxx，渲染结果列表。空结果展示暂无相关举报。搜索框保持当前关键词

**5.3 书籍详情页（BookDetailView）：** 调用 GET /api/books/{isbn}，渲染书籍信息+全部举报列表。举报列表按时间倒序，每条举报展示: 描述、证据(图片/视频/文字)、点赞/点踩按钮、当前票数。投票: 调用 POST /api/reports/{id}/vote，传递 IP+fingerprint。投票后更新本地票数状态

**5.4 举报表单（ReportView）：** 步骤1(可选): 上传书脊/ISBN 照片，调用 Tesseract.js OCR，回填 ISBN/书名/作者。步骤2: 表单字段(ISBN必填、书名必填、作者必填、描述必填)。步骤3: 上传封面(可选)+证据文件(可选，多选，支持图片/视频/文字)。表单校验: ISBN 格式、必填字段非空、描述不少于10字。提交: 调用 POST /api/reports(multipart/form-data)，成功后跳转书籍详情页。429 限流: 弹窗提示举报过于频繁，请稍后再试

**5.5 公共组件：** ReportCard(书籍卡片: 封面、书名、作者、ISBN、举报次数、时间)。SearchBox(搜索输入框: 防抖300ms，自动跳转)。FileUploader(多文件上传: 拖拽、预览、删除、MIME 校验)。VoteButton(点赞/点踩按钮: 绿色/红色、已投票态、票数显示)

### 5.6 任务 6：测试

**后端测试用例（pytest + httpx AsyncClient）：** POST /api/reports(新建书) -> 201，返回 report+book。POST /api/reports(ISBN已存在) -> 201，聚合到已有 book。POST /api/reports(限流触发) -> 429。GET /api/books/recent -> 200，<=20条，按 report_count 降序。GET /api/books/{isbn} -> 200，含全部 reports+evidences。GET /api/books/{不存在isbn} -> 404。GET /api/search?q=xxx -> 200，命中 title/author/description。POST /api/reports/{id}/vote -> 200，票数更新。POST /api/reports/{id}/vote(重复投票) -> 200，覆盖旧票。GET /api/feed/reports.rss -> 200，Content-Type: application/rss+xml

**前端测试用例（Vitest + Vue Test Utils）：** ReportCard 组件渲染 -> 正确显示封面、书名、作者、ISBN、举报次数。SearchBox 防抖 -> 输入停止 300ms 后才触发。VoteButton 投票 -> 点击后票数变化，再次点击取消。举报表单校验 -> 空 ISBN 报错，描述<10字报错。OCR 识别失败 -> 静默回退，不阻塞表单

**E2E 脚本（scripts/e2e.sh）：** curl 跑通 举报 -> 聚合 -> 搜索 -> 投票 -> RSS 全链路

### 5.7 任务 7：部署配置

**systemd 服务文件（/etc/systemd/system/aigbooks-api.service）：** [Unit] Description=AIGBooks API, After=network.target postgresql.service。[Service] Type=simple, User=www-data, WorkingDirectory=/opt/aigbooks/backend, Environment=AIGBOOKS_DATABASE_URL=postgresql+asyncpg://aigbooks:aigbooks@localhost:5432/aigbooks, ExecStart=/home/micray/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000, Restart=on-failure。[Install] WantedBy=multi-user.target

**nginx 配置片段：** server { listen 80; server_name aigbooks.example.com; client_max_body_size 20M; location /api/ { proxy_pass http://127.0.0.1:8000/api/; } location /evidence/ { alias /var/lib/aigbooks/evidence/; } location /covers/ { alias /var/lib/aigbooks/covers/; } location / { root /opt/aigbooks/frontend/dist; try_files  /index.html; } }

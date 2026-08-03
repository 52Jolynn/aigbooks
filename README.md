# AIGBooks

匿名 AI 生成书黑名单网站。FastAPI + PostgreSQL + Vue 3 单服务器部署。

---

## 项目介绍

**AIGBooks** 是一个**只读匿名 + 自由举报**的「AI 生成内容黑名单」网站，帮助读者在购书或订阅前快速识别并避开 AI 生成的劣质图书与期刊。

- **无账号体系**：不注册、不登录、不留存任何举报人身份
- **零审核**：提交即生效，无人工介入
- **本地识别**：支持上传图片、拍照识别、实时条码扫描三种模式
- **通用标识符**：以 `(type, identifier)` 二元组聚合，支持 ISBN-10/13、ISSN/ISSN-L
- **证据可查**：每次举报可附图片或视频证据，公开可见
- **结构化汇总**：按编号聚合全部举报与点赞/点踩，快速判断口碑

> 产品设计详见 `docs/plans/2026-07-29-aigbooks-design.md`。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy 2.0 async · PostgreSQL 15 / SQLite / MySQL · Alembic |
| 前端 | Vue 3 · Vite · TypeScript · Naive UI · Pinia · PaddleOCR（浏览器端 OCR）· Vue Router |
| 存储 | 本地磁盘（封面 + 证据） |
| 部署 | Docker Compose（systemd + nginx 单镜像方案参见 `deploy/docker/README.md`） |
| 构建 | 宿主机预构建前端 → `frontend-dist.tar.gz` → Dockerfile 单文件复制 + 解压 |
| Python | `>= 3.10`（推荐 3.12） |
| Node | `>= 22`（前端构建） |

---

## 项目结构

```
.
├── backend/            FastAPI 后端
│   ├── app/            业务代码（router / service / model / schema）
│   ├── alembic/        数据库迁移
│   ├── tests/          pytest 单元/集成测试
│   └── pyproject.toml  uv 项目配置
├── frontend/           Vue 3 前端
│   ├── src/            页面、组件、Pinia store、API 封装
│   └── package.json    pnpm 工作区
├── deploy/
│   └── docker/         Docker 构建脚本、nginx、entrypoint
├── docs/
│   ├── design/         设计文档
│   └── plans/          实施计划
├── scripts/            本地辅助脚本（如 API 列表）
├── docker-compose.yaml 一体化编排（PostgreSQL + 迁移 + 应用 + Nginx）
├── Dockerfile          多阶段镜像（后端 uv 安装依赖 + 复制预打包前端 → Python 运行时）
└── README.md
```

---

## 快速开始（源码开发）

### 1. 启动后端

```bash
cd backend
uv sync
cp .env.example .env          # 默认 SQLite，零依赖即可跑通
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

后端默认监听 `http://127.0.0.1:8000`，OpenAPI 文档：`http://127.0.0.1:8000/docs`。

切换到 PostgreSQL 时编辑 `backend/.env`：

```dotenv
AIGBOOKS_DATABASE_URL=postgresql+asyncpg://aigbooks:password@localhost:5432/aigbooks
```

### 2. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

前端开发服务器默认监听 `http://localhost:3000`，通过 Vite 代理转发 `/api`、`/ort-wasm`、`/models` 到后端。

### 3. 运行测试

```bash
# 后端
cd backend && uv run pytest -m "not e2e"

# 前端
cd frontend && pnpm test
```

代码检查：

```bash
cd backend  && uv run ruff check .
cd frontend && pnpm typecheck
```

---

## 构建方式

### A. 一体化 Docker 镜像（推荐，单服务器部署）

镜像采用多阶段构建：宿主机先用 Node 22 + pnpm 构建前端并打包为 `frontend-dist.tar.gz`，再用 `uv` 准备后端依赖，最后在 Python 3.12 slim 镜像中解压前端产物并运行 nginx + uvicorn。脚本会自动完成前端构建 → 打包 → 镜像构建 → 清理打包文件全流程。

宿主机需安装 **Node 22** 与 **pnpm 9**；如需在已具备 `frontend-dist.tar.gz` 的环境下跳过前端构建，可设置 `SKIP_FRONTEND_BUILD=1`；`KEEP_FRONTEND_BUNDLE=1` 可保留打包文件以便排错。

1. **准备环境变量**：在仓库根目录创建 `.env`

   ```dotenv
   POSTGRES_DB=aigbooks
   POSTGRES_USER=aigbooks
   POSTGRES_PASSWORD=请替换为强密码
   APP_PORT=8080
   ```

2. **构建镜像**（与本机 CPU 架构保持一致即可）

   ```bash
   bash deploy/docker/build-image.sh
   # 或显式指定：
   # PLATFORM=linux/arm64  IMAGE_TAG=arm64 bash deploy/docker/build-image.sh
   # PLATFORM=linux/amd64  IMAGE_TAG=amd64 bash deploy/docker/build-image.sh
   # SKIP_FRONTEND_BUILD=1 bash deploy/docker/build-image.sh   # 复用已生成的 frontend-dist.tar.gz
   ```

3. **启动编排**

   ```bash
   docker compose -f docker-compose.yaml up -d --build
   ```

   启动顺序：`db`（PostgreSQL 健康检查） → `migrate`（Alembic 迁移） → `app`（FastAPI + Nginx，监听 `8080`）。

4. **验证**

   ```bash
   curl -f http://localhost:8080/
   curl -f http://localhost:8080/api/openapi.json
   ```

   - 日志：`docker compose -f docker-compose.yaml logs -f app`
   - 停止：`docker compose -f docker-compose.yaml down`
   - 销毁数据卷：`docker compose -f docker-compose.yaml down -v`

> 详细说明与外部 PostgreSQL 用法参见 `deploy/docker/README.md`。

### B. 仅构建前端产物（静态托管/分离部署）

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm build
```

产物输出到 `frontend/dist/`，可部署到任意静态 Web 服务器，并将 `/api` 反向代理到后端。

### C. 仅构建后端 wheel/可执行包

`backend/pyproject.toml` 使用 `[tool.uv] package = false`，如需打包请移除该选项后：

```bash
cd backend
uv build
```

---

## 环境变量

后端通过 `AIGBOOKS_*` 前缀读取，关键项参见 `backend/.env.example`：

| 变量 | 说明 |
|------|------|
| `AIGBOOKS_DATABASE_URL` | SQLAlchemy 异步 URL（`sqlite+aiosqlite` / `postgresql+asyncpg` / `mysql+asyncmy`） |
| `AIGBOOKS_EVIDENCE_DIR` | 证据文件目录 |
| `AIGBOOKS_COVERS_DIR` | 封面图目录 |
| `AIGBOOKS_LOG_DIR` | 应用日志目录 |
| `AIGBOOKS_MAX_UPLOAD_SIZE` | 单封面上限（默认 20 MiB） |
| `AIGBOOKS_MAX_EVIDENCE_SIZE` | 单证据文件上限（默认 50 MiB） |
| `AIGBOOKS_REPORT_RATE_LIMIT` / `AIGBOOKS_REPORT_RATE_WINDOW` | 举报限流阈值与窗口 |
| `AIGBOOKS_CORS_ORIGINS` | 允许的跨域来源（JSON 数组） |

---

## 文档导航

- 产品设计：`docs/plans/2026-07-29-aigbooks-design.md`
- 实施计划：`docs/plans/2026-07-30-aigbooks-implementation-v2.md`
- Docker 部署：`deploy/docker/README.md`

---

## License

本项目基于 **Apache License 2.0** 开源，详见 `LICENSE` 文件。

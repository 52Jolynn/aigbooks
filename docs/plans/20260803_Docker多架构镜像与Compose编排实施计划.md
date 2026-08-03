---
创建时间: 2026-08-03 00:00
状态: 已完成
---

# 20260803 Docker 多架构镜像与 Compose 编排实施计划

## 计划概述
- **目标**：新增可在 amd64 或 arm64 主机上使用标准 Docker 构建应用镜像的脚本，并通过 Docker Compose 编排 Nginx、应用、数据库迁移和 PostgreSQL。
- **范围**：前端 Vue/Vite 构建产物与 FastAPI 后端合并到同一应用镜像；新增 PostgreSQL 服务、健康检查、迁移服务、持久化卷和部署说明。
- **不包含**：不修改业务 API、不改变前端 API 基路径、不将 PostgreSQL 打进应用镜像、不使用 Playwright。
- **预期成果**：`Dockerfile`、`.dockerignore`、标准 Docker 构建脚本、Compose 文件、Nginx 配置、容器部署文档。
- **成功标准**：本地 Compose 可启动 Nginx、应用、数据库迁移和 PostgreSQL；通过 Nginx 访问根路径返回 SPA，`/api/openapi.json` 可用；数据卷重启后保留；在对应 amd64/arm64 主机上均可使用标准 `docker build` 构建并运行。

## 需求背景
- **原始需求**：生成制作 Docker 镜像的脚本，支持 amd64、arm64 架构，前后端打包在一起，并提供 docker-compose 编排。
- **澄清结果**：采用应用单镜像、PostgreSQL 独立服务；Compose 提供 `app + postgres` 完整部署。
- **业务价值**：降低单机部署复杂度，支持 x86 服务器与 ARM 设备统一发布。

## 影响范围
- **新增文件**：`Dockerfile`、`.dockerignore`、`scripts/build-image.sh`、`compose.yaml`、`deploy/docker/entrypoint.sh`、`deploy/docker/README.md`。
- **修改文件**：`backend/app/main.py`（提供构建后的 SPA 静态资源和 SPA fallback，若当前实现不支持）；必要时修改 `backend/app/config.py` 的容器路径默认值。
- **数据库变更**：否。
- **第三方依赖**：否；沿用现有锁文件和依赖。

## 技术方案
1. 使用多阶段 Dockerfile：Node 阶段执行 `pnpm install --frozen-lockfile` 和 `pnpm build`；Python 阶段使用 uv 按目标平台安装生产依赖；最终镜像基于 Python slim，安装 `libmagic`，复制后端、虚拟环境和 `frontend/dist`。
2. 应用镜像仅运行 FastAPI；Nginx 作为独立 Compose 服务，负责 SPA 静态文件、history fallback、WASM MIME、缓存策略和 `/api`、`/covers`、`/evidence` 反向代理。前端构建产物复制到 Nginx 镜像。
3. Compose 使用 `db`、`migrate`、`app` 三个服务：`db` 以 `pg_isready` 做健康检查；`migrate` 等待数据库健康后运行 `alembic upgrade head`；`app` 依赖迁移成功后启动。
4. 应用数据、封面、证据使用持久化卷；数据库使用独立 PostgreSQL 卷；数据库端口默认不发布到宿主机。
5. 不使用 Docker Buildx。构建脚本使用标准 `docker build`，通过当前 Docker 主机架构构建对应镜像；需要同时发布两种架构时，分别在 amd64 和 arm64 构建机执行并推送相同标签，部署时由仓库/发布流程管理架构标签。

## 任务分解

### 任务1：实现单镜像构建
- 新增多阶段 `Dockerfile`，避免复制宿主机 `node_modules` 或跨架构 Python 环境。
- 新增 `.dockerignore`，排除 Git、缓存、虚拟环境、依赖目录和本地数据库，同时保留前端 `public` 模型/WASM资源。
- 新增 `scripts/build-image.sh`，使用标准 `docker build`，支持镜像名、标签和构建架构标识参数，不调用 Buildx。

### 任务2：新增 Nginx 生产网关
- 新增 Nginx Dockerfile/配置，将前端 `dist` 放入 Nginx 镜像。
- 配置 SPA fallback、`/api`、`/covers`、`/evidence` 反代、上传体积限制、WASM MIME 和缓存策略。
- 应用镜像只负责 FastAPI 后端，不再承担前端静态资源服务。

### 任务3：新增 Compose 编排
- 新增 `compose.yaml`，定义 `db`、`migrate`、`app`、`nginx`。
- 为数据库增加健康检查，为迁移单独执行 Alembic；Nginx 等待应用健康后提供入口。
- 挂载 PostgreSQL、应用数据、封面、证据和日志卷；密码使用环境变量，不写死在仓库。

### 任务4：完善部署说明
- 新增 Docker 部署 README，说明 `.env` 配置、构建/推送、启动/停止、迁移、日志、备份和 amd64/arm64 验证命令。
- 明确 Compose 内部数据库地址必须使用 `db`，以及如何改为外部 PostgreSQL。

### 任务5：验证
- 运行前端 `npm run lint`、`npm run typecheck`，后端 ruff/typecheck 可用命令并执行。
- 使用 `docker compose config` 校验编排文件。
- 如 Docker 环境可用，执行镜像构建和 Compose 健康检查；不使用 Playwright。

## 风险与应对
| 风险 | 概率 | 影响 | 应对措施 |
|---|---:|---:|---|
| 非 SQLite 未自动迁移 | 高 | 高 | 独立 `migrate` 服务并设置完成依赖 |
| arm64 原生依赖不兼容 | 中 | 高 | 目标平台安装依赖，使用 Python slim，不复制宿主机环境 |
| OCR 模型/WASM 被忽略 | 中 | 高 | `.dockerignore` 仅排除缓存，显式验证资源路径 |
| 容器重建丢失上传文件 | 高 | 高 | 独立命名卷挂载 `var` 数据目录 |
| SPA 深层路由 404 | 中 | 中 | 增加 fallback，并使用 API/静态路径优先匹配 |

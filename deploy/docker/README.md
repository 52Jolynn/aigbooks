# Docker 部署

## 1. 配置

在项目根目录创建 `.env`：

```dotenv
POSTGRES_DB=aigbooks
POSTGRES_USER=aigbooks
POSTGRES_PASSWORD=请替换为强密码
APP_PORT=8080
```

Compose 内部使用 `db` 作为 PostgreSQL 主机名，不要填写 `localhost`。

## 2. 构建镜像

标准 `docker build` 按当前主机架构构建，不使用 Buildx：

```bash
bash deploy/docker/build-image.sh
```

在 ARM 主机上构建：

```bash
PLATFORM=linux/arm64 IMAGE_TAG=arm64 bash deploy/docker/build-image.sh
```

在 amd64 主机上构建：

```bash
PLATFORM=linux/amd64 IMAGE_TAG=amd64 bash deploy/docker/build-image.sh
```

Compose 默认直接构建对应主机架构的应用镜像和 Nginx 镜像。

## 3. 启动

```bash
docker compose -f docker-compose.yaml up -d --build
```

启动顺序为 PostgreSQL 健康检查、Alembic 迁移、FastAPI 应用、Nginx。访问 `http://localhost:8080`。

查看状态和日志：

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs -f app
```

停止服务：

```bash
docker compose -f docker-compose.yaml down
```

删除服务及数据卷：

```bash
docker compose -f docker-compose.yaml down -v
```

## 4. 验证

```bash
curl -f http://localhost:8080/
curl -f http://localhost:8080/api/openapi.json
```

OCR 资源应返回成功响应：

```bash
curl -I http://localhost:8080/ort-wasm/ort-wasm-simd-threaded.jsep.wasm
curl -I http://localhost:8080/models/PP-OCRv5_mobile_det.tar
```

## 5. 数据与备份

Compose 使用 `postgres-data` 保存 PostgreSQL 数据，使用 `app-data` 保存封面、证据和日志。备份 PostgreSQL 时使用 `pg_dump`，并同时备份应用数据卷。

## 6. 使用外部 PostgreSQL

如需连接外部 PostgreSQL，可复制 `docker-compose.yaml` 为覆盖文件，移除 `db` 和 `migrate` 的数据库服务依赖，并将 `AIGBOOKS_DATABASE_URL` 改为外部地址。应用镜像仍由 `app` 服务运行，Nginx 入口不变。

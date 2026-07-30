# AIGBooks 单服务器部署指南

本文档面向 Ubuntu 22.04+ / Debian 12+ 单服务器部署。

## 1. 前置依赖

```bash
sudo apt update
sudo apt install -y postgresql-15 nginx curl jq uuid-runtime
```

安装 uv（Python 包管理器）：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. PostgreSQL 准备

```bash
sudo -u postgres psql <<SQL
CREATE USER aigbooks WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE aigbooks OWNER aigbooks;
GRANT ALL PRIVILEGES ON DATABASE aigbooks TO aigbooks;
SQL
```

## 3. 文件目录

```bash
sudo mkdir -p /opt/aigbooks /var/lib/aigbooks/{covers,evidence} /etc/aigbooks
sudo chown -R www-data:www-data /opt/aigbooks /var/lib/aigbooks /etc/aigbooks
```

## 4. 部署代码

```bash
sudo -u www-data git clone <REPO_URL> /opt/aigbooks
cd /opt/aigbooks/backend
sudo -u www-data uv sync
```

## 5. 数据库迁移

```bash
sudo -u www-data \
  AIGBOOKS_DATABASE_URL="postgresql+asyncpg://aigbooks:CHANGE_ME@localhost:5432/aigbooks" \
  uv run alembic upgrade head
```

## 6. 配置环境变量

```bash
sudo tee /etc/aigbooks/api.env <<EOF
AIGBOOKS_DATABASE_URL=postgresql+asyncpg://aigbooks:CHANGE_ME@localhost:5432/aigbooks
AIGBOOKS_EVIDENCE_DIR=/var/lib/aigbooks/evidence
AIGBOOKS_COVERS_DIR=/var/lib/aigbooks/covers
AIGBOOKS_CORS_ORIGINS=["https://aigbooks.example.com"]
EOF
sudo chmod 600 /etc/aigbooks/api.env
```

## 7. 构建前端

```bash
cd /opt/aigbooks/frontend
sudo -u www-data pnpm install --frozen-lockfile
sudo -u www-data pnpm build
```

## 8. systemd 服务

```bash
sudo cp /opt/aigbooks/deploy/aigbooks-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aigbooks-api
sudo systemctl status aigbooks-api
```

预期日志：`AIGBooks API started`。

## 9. nginx 配置

```bash
sudo cp /opt/aigbooks/deploy/nginx-aigbooks.conf /etc/nginx/sites-available/aigbooks
sudo ln -s /etc/nginx/sites-available/aigbooks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 10. HTTPS（可选）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aigbooks.example.com
```

certbot 会自动修改 nginx 配置并启用 HTTP/2 + 续签。

## 11. E2E 冒烟

```bash
AIGBOOKS_API=http://localhost:8000 bash /opt/aigbooks/scripts/e2e.sh
```

应输出 `✅ E2E 全部通过`。

## 12. 升级流程

```bash
cd /opt/aigbooks
sudo -u www-data git pull

# 后端
cd backend
sudo -u www-data uv sync
sudo -u www-data uv run alembic upgrade head
sudo systemctl restart aigbooks-api

# 前端
cd ../frontend
sudo -u www-data pnpm install --frozen-lockfile
sudo -u www-data pnpm build
```

## 13. 故障排查

| 现象 | 排查 |
|---|---|
| 502 Bad Gateway | `systemctl status aigbooks-api`；`journalctl -u aigbooks-api -n 50` |
| 静态资源 404 | 检查 `/opt/aigbooks/frontend/dist/` 存在；`nginx -t` |
| 上传 413 | nginx `client_max_body_size 25M`；FastAPI `AIGBOOKS_MAX_UPLOAD_SIZE=20971520` |
| DB 连接错 | `AIGBOOKS_DATABASE_URL` 格式；`pg_isready -h localhost` |
| OCR 不工作 | Tesseract.js WASM 由 CDN 加载（Fontsource 自托管字体不影响） |

## 14. 安全建议

- 定期 `apt upgrade`
- 配置 UFW：`ufw allow 22,80,443/tcp`
- 配置 fail2ban
- 监控：`journalctl -u aigbooks-api -f`
- 备份：定期 `pg_dump aigbooks` + 备份 `/var/lib/aigbooks/evidence`

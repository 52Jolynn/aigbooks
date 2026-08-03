FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /src/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM ghcr.io/astral-sh/uv:0.8.14 AS backend-dependencies

WORKDIR /src/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:$PATH" \
    AIGBOOKS_EVIDENCE_DIR=/app/var/evidence \
    AIGBOOKS_COVERS_DIR=/app/var/covers \
    AIGBOOKS_LOG_DIR=/app/var/logs

RUN apt-get update \
    && apt-get install --no-install-recommends -y libmagic1 nginx tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin aigbooks

WORKDIR /app/backend
COPY --from=backend-dependencies /src/backend/.venv /app/backend/.venv
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /src/frontend/dist /usr/share/nginx/html
COPY deploy/docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/listen 80;/listen 8080;/' /etc/nginx/conf.d/default.conf \
    && sed -i 's/proxy_pass http:\/\/app:8000/proxy_pass http:\/\/127.0.0.1:8000/' /etc/nginx/conf.d/default.conf \
    && mkdir -p /app/var/covers /app/var/evidence /app/var/logs /var/log/nginx /var/lib/nginx /run \
    && touch /run/nginx.pid \
    && chown -R aigbooks:aigbooks /app /var/log/nginx /var/lib/nginx /run/nginx.pid \
    && chmod +x /entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "2"]
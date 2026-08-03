FROM python:3.12-slim-bookworm AS backend-dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.9.21

WORKDIR /app/backend
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
COPY --from=backend-dependencies /app/backend/.venv /app/backend/.venv
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend-dist.tar.gz /tmp/frontend-dist.tar.gz
COPY deploy/docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/listen 80;/listen 8080;/' /etc/nginx/conf.d/default.conf \
    && sed -i 's/proxy_pass http:\/\/app:8000/proxy_pass http:\/\/127.0.0.1:8000/' /etc/nginx/conf.d/default.conf \
    && tar -xzf /tmp/frontend-dist.tar.gz -C /usr/share/nginx/html --strip-components=1 \
    && rm /tmp/frontend-dist.tar.gz \
    && test -f /usr/share/nginx/html/index.html \
    && mkdir -p /app/var/covers /app/var/evidence /app/var/logs /var/log/nginx /var/lib/nginx /run \
    && touch /run/nginx.pid \
    && chown -R aigbooks:aigbooks /app /var/log/nginx /var/lib/nginx /run/nginx.pid \
    && chmod +x /entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "2"]
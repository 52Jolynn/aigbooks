"""AIGBooks FastAPI 入口。"""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.db.constants import DIALECT_SQLITE
from app.db.dialect import current_dialect, parse_dialect
from app.logging_config import setup_logging
from app.middleware.exception import register_exception_handlers
from app.routers.feed import router as feed_router
from app.routers.identifiers import router as identifiers_router
from app.routers.reports import router as reports_router
from app.routers.search import router as search_router
from app.utils.tokenize import warmup as warmup_jieba

logger = logging.getLogger("aigbooks")

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _run_alembic_upgrade(settings: Settings) -> None:
    """SQLite 自动迁移：跨 worker 文件锁互斥；子进程隔离事件循环。

    用子进程跑 ``alembic upgrade head`` 彻底避免 alembic 自带的
    ``asyncio.run()`` 与 uvicorn/aiosqlite 在 lifespan 上下文里竞争。

    非 SQLite（生产 PG/MySQL）保持「运维手动 alembic upgrade」语义，
    避免应用启动期对生产库产生意料之外的 DDL。
    """
    try:
        dialect = parse_dialect(settings.database_url)
    except ValueError:
        logger.warning("alembic auto-migrate skipped: invalid database_url")
        return
    if dialect != DIALECT_SQLITE:
        logger.info("alembic auto-migrate skipped: dialect=%s (non-sqlite)", dialect)
        return

    lock_path = _BACKEND_DIR / "var" / "migrate.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(_BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.error(
                "alembic upgrade head failed (rc=%d)\nstdout=%s\nstderr=%s",
                result.returncode,
                result.stdout,
                result.stderr,
            )
        else:
            logger.info("alembic upgrade head done")
    except subprocess.TimeoutExpired:
        logger.error("alembic upgrade head timed out after 30s")
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logger.info("running alembic upgrade head (sqlite auto-migrate) …")
    await run_in_threadpool(_run_alembic_upgrade, settings)
    setup_logging(settings)
    logger.info("AIGBooks API started, dialect=%s", current_dialect())
    await run_in_threadpool(warmup_jieba)
    yield
    logger.info("AIGBooks API stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)

    app = FastAPI(
        title="AIGBooks API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/covers",
        StaticFiles(directory=str(settings.covers_dir.resolve()), check_dir=False),
        name="covers",
    )
    app.mount(
        "/evidence",
        StaticFiles(directory=str(settings.evidence_dir.resolve()), check_dir=False),
        name="evidence",
    )

    register_exception_handlers(app)
    app.include_router(identifiers_router, prefix="/api", tags=["identifiers"])
    app.include_router(reports_router, prefix="/api", tags=["reports"])
    app.include_router(search_router, prefix="/api", tags=["search"])
    app.include_router(feed_router, prefix="/api", tags=["feed"])

    return app


app = create_app()

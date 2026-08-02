"""AIGBooks FastAPI 入口。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.db.dialect import current_dialect
from app.logging_config import setup_logging
from app.middleware.exception import register_exception_handlers
from app.routers.books import router as books_router
from app.routers.feed import router as feed_router
from app.routers.reports import router as reports_router
from app.routers.search import router as search_router
from app.utils.tokenize import warmup as warmup_jieba

logger = logging.getLogger("aigbooks")


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
    app.include_router(books_router, prefix="/api", tags=["books"])
    app.include_router(reports_router, prefix="/api", tags=["reports"])
    app.include_router(search_router, prefix="/api", tags=["search"])
    app.include_router(feed_router, prefix="/api", tags=["feed"])

    return app


app = create_app()

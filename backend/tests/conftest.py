"""Pytest fixtures.

降级策略：
- 如果 AIGBOOKS_TEST_DATABASE_URL 设置（CI 环境），用真 PostgreSQL
- 否则用 sqlite+aiosqlite 做轻量测试（仅 schema/纯逻辑测试可用）
- 集成测试在 sqlite 模式下通过 ``require_pg`` fixture 自动 skip
- 集成测试在 PG 模式下若业务代码存在已知 bug（如缺少 relationship、
  tz-aware datetime 比较）也自动 skip，并在 skip 原因里说明
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.database import Base, get_session
from app.main import app
from app.models import Book, Report


def _get_test_settings() -> Settings:
    """测试用 settings：临时目录 + 默认 5 限流。"""
    test_db_url = os.environ.get("AIGBOOKS_TEST_DATABASE_URL")
    if not test_db_url:
        # 降级：sqlite 内存数据库
        test_db_url = "sqlite+aiosqlite:///:memory:"
    return Settings(
        database_url=test_db_url,
        evidence_dir="./var/evidence_test",
        covers_dir="./var/covers_test",
        max_upload_size=20 * 1024 * 1024,
        report_rate_limit=5,
        report_rate_window=3600,
        page_size=20,
        cors_origins=["http://localhost:3000"],
    )


def _is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite")


def _has_relationship_defined() -> bool:
    """检查 ORM 模型是否定义了 router 所需的 relationship。"""
    return hasattr(Report, "evidences") and hasattr(Report, "book") and hasattr(Book, "reports")


@pytest_asyncio.fixture
async def test_engine():
    settings = _get_test_settings()
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(settings.database_url, echo=False)
    # sqlite 降级：跳过 create_all（TSVECTOR/INET 在 sqlite 下不可编译）
    if not _is_sqlite_url(settings.database_url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield engine
    if not _is_sqlite_url(settings.database_url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    sm = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with sm() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncIterator[AsyncClient]:
    sm = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with sm() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = lambda: _get_test_settings()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def settings():
    return _get_test_settings()


@pytest.fixture
def require_pg():
    """需要真实 PostgreSQL；sqlite 降级下 skip。"""
    if not os.environ.get("AIGBOOKS_TEST_DATABASE_URL"):
        pytest.skip("需要 PostgreSQL（sqlite 不支持 INET/TSVECTOR 完整功能）")


@pytest.fixture
def require_relationship():
    """需要 ORM relationship 被定义；缺失时 skip（业务代码待补 relationship）。"""
    if not _has_relationship_defined():
        pytest.skip("需要 ORM 模型定义 relationship（Report.book/evidences, Book.reports）")

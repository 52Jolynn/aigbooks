"""Pytest fixtures.

增强后支持三方言矩阵：
- PostgreSQL：通过 ``AIGBOOKS_TEST_DATABASE_URL`` 指定，集成测试可用
- SQLite（默认）：自动建主表 + FTS5 虚拟表 + 同步触发器，所有测试可用
- MySQL：通过 ``AIGBOOKS_TEST_DATABASE_URL_MYSQL`` 指定

方言跳过辅助：
- ``require_dialect(name)``：当前 dialect 不匹配时 skip
- ``require_pg``：保留为 ``require_dialect("postgresql")`` 别名
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.database import Base, get_session
from app.db.constants import DIALECT_POSTGRESQL, URL_SCHEME_SQLITE
from app.db.dialect import parse_dialect
from app.main import app
from app.models import Book, Report

_SQLITE_FTS5_DDL = [
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
        search_text,
        content='books', content_rowid='id',
        tokenize='unicode61'
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5(
        search_text,
        content='reports', content_rowid='id',
        tokenize='unicode61'
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_ai AFTER INSERT ON books BEGIN
        INSERT INTO books_fts(rowid, search_text) VALUES (new.id, new.search_text);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_ad AFTER DELETE ON books BEGIN
        INSERT INTO books_fts(books_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_au AFTER UPDATE ON books BEGIN
        INSERT INTO books_fts(books_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
        INSERT INTO books_fts(rowid, search_text) VALUES (new.id, new.search_text);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS reports_fts_ai AFTER INSERT ON reports BEGIN
        INSERT INTO reports_fts(rowid, search_text) VALUES (new.id, new.search_text);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS reports_fts_ad AFTER DELETE ON reports BEGIN
        INSERT INTO reports_fts(reports_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS reports_fts_au AFTER UPDATE ON reports BEGIN
        INSERT INTO reports_fts(reports_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
        INSERT INTO reports_fts(rowid, search_text) VALUES (new.id, new.search_text);
    END
    """,
]


def _sqlite_url() -> str:
    return "sqlite+aiosqlite:///:memory:"


def _get_test_settings(db_url: str | None = None) -> Settings:
    url = db_url or os.environ.get("AIGBOOKS_TEST_DATABASE_URL") or _sqlite_url()
    return Settings(
        database_url=url,
        evidence_dir="./var/evidence_test",
        covers_dir="./var/covers_test",
        max_upload_size=20 * 1024 * 1024,
        report_rate_limit=5,
        report_rate_window=3600,
        page_size=20,
        cors_origins=["http://localhost:3000"],
    )


def _is_sqlite_url(url: str) -> bool:
    return url.startswith(URL_SCHEME_SQLITE)


def _has_relationship_defined() -> bool:
    return hasattr(Report, "evidences") and hasattr(Report, "book") and hasattr(Book, "reports")


@pytest.fixture
def test_db_url() -> str:
    """当前测试使用的数据库 URL（默认 SQLite 内存）。"""
    return os.environ.get("AIGBOOKS_TEST_DATABASE_URL") or _sqlite_url()


@pytest.fixture
def test_dialect(test_db_url: str) -> str:
    return parse_dialect(test_db_url)


@pytest.fixture(autouse=True)
def _patch_dialect(monkeypatch, test_db_url: str):
    """根据 ``test_db_url`` 覆盖 ``current_dialect`` 返回值。"""
    from app.db import dialect as dialect_module
    from app.db.search import reset_search_backend

    dialect = parse_dialect(test_db_url)
    monkeypatch.setattr(dialect_module, "current_dialect", lambda: dialect)
    reset_search_backend()
    yield
    reset_search_backend()


@pytest_asyncio.fixture
async def test_engine(test_db_url: str):
    settings = _get_test_settings(test_db_url)
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if _is_sqlite_url(settings.database_url):
            for ddl in _SQLITE_FTS5_DDL:
                await conn.execute(text(ddl))

    yield engine

    async with engine.begin() as conn:
        if _is_sqlite_url(settings.database_url):
            await conn.execute(text("DROP TRIGGER IF EXISTS reports_fts_au"))
            await conn.execute(text("DROP TRIGGER IF EXISTS reports_fts_ad"))
            await conn.execute(text("DROP TRIGGER IF EXISTS reports_fts_ai"))
            await conn.execute(text("DROP TRIGGER IF EXISTS books_fts_au"))
            await conn.execute(text("DROP TRIGGER IF EXISTS books_fts_ad"))
            await conn.execute(text("DROP TRIGGER IF EXISTS books_fts_ai"))
            await conn.execute(text("DROP TABLE IF EXISTS reports_fts"))
            await conn.execute(text("DROP TABLE IF EXISTS books_fts"))
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    sm = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with sm() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_db_url: str, test_engine) -> AsyncIterator[AsyncClient]:
    sm = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    settings = _get_test_settings(test_db_url)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with sm() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def settings(test_db_url: str) -> Settings:
    return _get_test_settings(test_db_url)


@pytest.fixture
def require_dialect(test_dialect: str):
    """仅在指定方言下运行；不匹配则 skip。"""

    def _require(name: str) -> None:
        if test_dialect != name:
            pytest.skip(f"only runs on {name}; current dialect is {test_dialect}")

    return _require


@pytest.fixture
def require_pg(require_dialect):
    """向后兼容：仅 PostgreSQL。"""
    require_dialect(DIALECT_POSTGRESQL)


@pytest.fixture
def require_relationship() -> None:
    if not _has_relationship_defined():
        pytest.skip("需要 ORM 模型定义 relationship（Report.book/evidences, Book.reports）")

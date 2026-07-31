"""SQLAlchemy 2.0 异步数据库连接与 Session 工厂。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.db.constants import DIALECT_SQLITE
from app.db.dialect import current_dialect


class Base(DeclarativeBase):
    """所有 ORM Model 的基类。"""


_settings = get_settings()
_dialect = current_dialect()

_engine_kwargs: dict = {"echo": _settings.database_echo}
if _dialect != DIALECT_SQLITE:
    _engine_kwargs["pool_pre_ping"] = True
else:
    _engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}

async_engine = create_async_engine(_settings.database_url, **_engine_kwargs)


def _set_sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
    """SQLite 连接初始化：WAL + busy_timeout + synchronous + foreign_keys。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


if _dialect == DIALECT_SQLITE:
    event.listen(async_engine.sync_engine, "connect", _set_sqlite_pragmas)


async_sessionmaker_instance = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：每个请求一个 AsyncSession。"""
    async with async_sessionmaker_instance() as session:
        yield session

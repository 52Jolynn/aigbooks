"""数据库方言识别：基于 SQLAlchemy URL schema 返回标准方言名。"""

from __future__ import annotations

from typing import Literal

DialectName = Literal["postgresql", "sqlite", "mysql"]

_URL_TO_DIALECT: dict[str, DialectName] = {
    "postgresql+asyncpg": "postgresql",
    "sqlite+aiosqlite": "sqlite",
    "mysql+asyncmy": "mysql",
}


def parse_dialect(url: str) -> DialectName:
    """从 ``database_url`` 解析方言名。

    Raises:
        ValueError: URL scheme 不在受支持驱动列表中。
    """
    scheme = url.split("://", 1)[0]
    dialect = _URL_TO_DIALECT.get(scheme)
    if dialect is None:
        supported = ", ".join(sorted(_URL_TO_DIALECT.keys()))
        raise ValueError(
            f"Unsupported database driver: {scheme!r}. Supported drivers: {supported}"
        )
    return dialect


def current_dialect() -> DialectName:
    """从全局 ``Settings`` 读取当前方言名。"""
    from app.config import get_settings

    return parse_dialect(get_settings().database_url)

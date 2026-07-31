"""数据库方言识别：基于 SQLAlchemy URL schema 返回标准方言名。

方言名称与 URL scheme 常量化于 :mod:`app.db.constants`。
"""

from __future__ import annotations

from app.db.constants import (
    SUPPORTED_URL_PREFIXES,
    URL_SCHEME_TO_DIALECT,
    DialectName,
)


def parse_dialect(url: str) -> DialectName:
    """从 ``database_url`` 解析方言名。

    Raises:
        ValueError: URL scheme 不在受支持驱动列表中。
    """
    scheme = url.split("://", 1)[0]
    dialect = URL_SCHEME_TO_DIALECT.get(scheme)
    if dialect is None:
        raise ValueError(
            f"Unsupported database driver: {scheme!r}. Supported drivers: {SUPPORTED_URL_PREFIXES}"
        )
    return dialect


def current_dialect() -> DialectName:
    """从全局 ``Settings`` 读取当前方言名。"""
    from app.config import get_settings

    return parse_dialect(get_settings().database_url)

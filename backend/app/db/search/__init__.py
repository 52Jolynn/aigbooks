"""全文检索抽象：按当前方言返回对应 ``SearchBackend`` 实现。"""

from __future__ import annotations

from typing import Protocol

from app.db import dialect as _dialect_module
from app.db.constants import (
    DIALECT_MYSQL,
    DIALECT_POSTGRESQL,
    DIALECT_SQLITE,
)
from app.db.search.mysql import MysqlSearchBackend
from app.db.search.postgres import PostgresSearchBackend
from app.db.search.sqlite import SqliteSearchBackend


class SearchBackend(Protocol):
    """全文检索 backend 接口。"""

    async def search_report_ids(
        self,
        db,  # noqa: ANN001
        q: str,
        page_size: int,
    ) -> tuple[list[int], str]:
        """返回 ``(report_id 列表, 清洗后查询字符串)``。"""
        ...


_BACKENDS: dict[str, type[SearchBackend]] = {
    DIALECT_POSTGRESQL: PostgresSearchBackend,
    DIALECT_SQLITE: SqliteSearchBackend,
    DIALECT_MYSQL: MysqlSearchBackend,
}

_instance: SearchBackend | None = None


def get_search_backend() -> SearchBackend:
    """单例工厂：按 ``current_dialect()`` 返回对应 backend。

    通过模块属性查找调用 :func:`current_dialect`，便于测试 monkeypatch。
    """
    global _instance
    if _instance is None:
        _instance = _BACKENDS[_dialect_module.current_dialect()]()
    return _instance


def reset_search_backend() -> None:
    """测试钩子：清空单例以便重新选择 backend。"""
    global _instance
    _instance = None

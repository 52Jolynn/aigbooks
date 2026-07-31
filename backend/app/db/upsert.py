"""跨方言 UPSERT 抽象：封装 ``ON CONFLICT`` / ``ON DUPLICATE KEY UPDATE``。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Insert
from sqlalchemy.dialects import mysql, postgresql, sqlite

from app.db.dialect import current_dialect


def _dialect_insert():
    dialect = current_dialect()
    if dialect == "postgresql":
        return postgresql.insert
    if dialect == "sqlite":
        return sqlite.insert
    if dialect == "mysql":
        return mysql.insert
    raise ValueError(f"Unsupported dialect: {dialect}")


def _default_update_set(rows: list[dict[str, Any]], conflict_keys: list[str]) -> dict[str, Any]:
    """从首行推断非冲突键的全部列。"""
    if not rows:
        return {}
    return {k: v for k, v in rows[0].items() if k not in conflict_keys and k != "id"}


def make_upsert(
    model: type,
    rows: list[dict[str, Any]],
    conflict_keys: list[str],
    update_set: dict[str, Any] | None = None,
) -> Insert:
    """构造 UPSERT 语句。

    Args:
        model: ORM 模型类。
        rows: 待插入数据。
        conflict_keys: 唯一约束列名，参与 ``ON CONFLICT`` / ``ON DUPLICATE KEY UPDATE``。
        update_set: 冲突时更新的列与值；``None`` 时默认更新非冲突键的全部列。

    Returns:
        ``sqlalchemy.Insert`` 对象，可直接传入 ``await session.execute()``。
    """
    insert_fn = _dialect_insert()
    stmt = insert_fn(model).values(rows)

    effective_set = (
        update_set if update_set is not None else _default_update_set(rows, conflict_keys)
    )

    if current_dialect() == "mysql":
        return stmt.on_duplicate_key_update(effective_set)
    return stmt.on_conflict_do_update(index_elements=conflict_keys, set_=effective_set)

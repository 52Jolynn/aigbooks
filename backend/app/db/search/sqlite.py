"""SQLite 全文检索：FTS5 影子表 + jieba 切词。

写入侧：ORM event listener 用 jieba ``cut_for_search`` 把标题/作者/描述切成词，
空格拼接后写入 ``search_text`` 列；触发器自动同步到 ``books_fts`` / ``reports_fts``
FTS5 影子表（``tokenize='unicode61'``，词间空格分隔即可被 unicode61 视为独立 token）。

查询侧：同样用 jieba 切词 → 拼成 FTS5 ``MATCH`` 表达式（多 token OR）。
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.text import sanitize_query
from app.utils.tokenize import cut_for_search


class SqliteSearchBackend:
    """SQLite 主路径：FTS5 ``MATCH`` over ``books_fts`` / ``reports_fts``。"""

    async def search_report_ids(
        self,
        db: AsyncSession,
        q: str,
        page_size: int,
    ) -> tuple[list[int], str]:
        cleaned = sanitize_query(q)
        if not cleaned:
            return [], q

        tokens = cut_for_search(cleaned)
        if not tokens:
            return [], cleaned

        match_query = " ".join(tokens)
        sql = text(
            """
            SELECT r.id
            FROM reports r
            WHERE r.id IN (SELECT rowid FROM reports_fts WHERE reports_fts MATCH :q)
               OR r.book_id IN (SELECT rowid FROM books_fts WHERE books_fts MATCH :q)
            ORDER BY r.created_at DESC
            LIMIT :limit
            """
        )
        result = await db.execute(sql, {"q": match_query, "limit": page_size})
        ids = [row[0] for row in result.fetchall()]
        return ids, cleaned

"""PostgreSQL 全文检索：``websearch_to_tsquery`` + GIN 索引。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.text import sanitize_query


class PostgresSearchBackend:
    """PG 主路径：``tsv_desc @@ websearch_to_tsquery('simple', q)`` OR ``tsv_meta``。

    - ``tsv_desc`` / ``tsv_meta`` 由 DB 触发器维护（migration 002_multidb 中创建）
    - 使用 ``simple`` configuration（无词形还原，对中文按字符切分）
    """

    async def search_report_ids(
        self,
        db: AsyncSession,
        q: str,
        page_size: int,
    ) -> tuple[list[int], str]:
        cleaned = sanitize_query(q)
        if not cleaned:
            return [], q

        sql = text(
            """
            SELECT r.id
            FROM reports r
            JOIN identifiers b ON b.id = r.identifier_id
            WHERE r.tsv_desc @@ websearch_to_tsquery('simple', :q)
               OR b.tsv_meta @@ websearch_to_tsquery('simple', :q)
            ORDER BY r.created_at DESC
            LIMIT :limit
            """
        )
        result = await db.execute(sql, {"q": cleaned, "limit": page_size})
        ids = [row[0] for row in result.fetchall()]
        return ids, cleaned

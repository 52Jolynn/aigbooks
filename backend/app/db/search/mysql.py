"""MySQL 全文检索：``FULLTEXT ... WITH PARSER ngram`` + ``MATCH ... AGAINST``。"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.text import sanitize_query


class MysqlSearchBackend:
    """MySQL 主路径：``MATCH ... AGAINST(:q IN BOOLEAN MODE)``。

    - 索引由 migration 002_multidb 创建：
      ``FULLTEXT KEY ... (description) WITH PARSER ngram`` 等
    - ngram parser 按字符 2-gram 切分，对中文凑合可用
    - BOOLEAN MODE 支持 ``+word -word`` 等查询语法
    - DBA 需配置 ``innodb_ft_min_token_size=2`` 以提升中文单字召回
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
            JOIN books b ON b.id = r.book_id
            WHERE MATCH(r.description) AGAINST(:q IN BOOLEAN MODE)
               OR MATCH(b.title, b.author) AGAINST(:q IN BOOLEAN MODE)
            ORDER BY r.created_at DESC
            LIMIT :limit
            """
        )
        result = await db.execute(sql, {"q": cleaned, "limit": page_size})
        ids = [row[0] for row in result.fetchall()]
        return ids, cleaned

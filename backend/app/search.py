"""搜索：PG FTS（websearch_to_tsquery） + ILIKE 回退。"""

from __future__ import annotations

import re

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Book, Report

# tsquery 元字符：过滤掉，仅保留简单关键字
_SPECIAL_CHARS = re.compile(r"[():&|!*\"'<>\-]")


def sanitize_query(q: str) -> str:
    """清洗搜索关键词：去除 tsquery 特殊字符与多余空白。"""
    q = _SPECIAL_CHARS.sub(" ", q).strip()
    q = re.sub(r"\s+", " ", q)
    return q


async def search_reports(
    db: AsyncSession, q: str, page_size: int | None = None
) -> tuple[list[Report], str]:
    """搜索举报。返回 ``(reports, cleaned_query)``。

    - 清洗后为空 → ILIKE 模糊
    - 清洗后非空 → PG websearch_to_tsquery（同时匹配 r.tsv_desc 与 b.tsv_meta）
    """
    settings = get_settings()
    page_size = page_size or settings.page_size

    cleaned = sanitize_query(q)

    if not cleaned:
        like = f"%{q}%"
        stmt = (
            select(Report)
            .join(Book, Book.id == Report.book_id)
            .options(selectinload(Report.book), selectinload(Report.evidences))
            .where(
                or_(
                    Book.title.ilike(like),
                    Book.author.ilike(like),
                    Report.description.ilike(like),
                )
            )
            .order_by(Report.created_at.desc())
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return list(result.scalars().unique().all()), q

    fts_sql = text(
        """
        SELECT r.id
        FROM reports r
        JOIN books b ON b.id = r.book_id
        WHERE r.tsv_desc @@ websearch_to_tsquery('simple', :q)
           OR b.tsv_meta @@ websearch_to_tsquery('simple', :q)
        ORDER BY r.created_at DESC
        LIMIT :limit
        """
    )
    fts_result = await db.execute(fts_sql, {"q": cleaned, "limit": page_size})
    ids = [row[0] for row in fts_result.fetchall()]
    if not ids:
        return [], cleaned

    stmt = (
        select(Report)
        .where(Report.id.in_(ids))
        .options(selectinload(Report.book), selectinload(Report.evidences))
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all()), cleaned

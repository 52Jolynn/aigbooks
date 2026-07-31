"""搜索：委托给 ``SearchBackend``；清洗后为空时 ILIKE/LIKE 回退。"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.search import get_search_backend
from app.models import Book, Report


async def search_reports(
    db: AsyncSession, q: str, page_size: int | None = None
) -> tuple[list[Report], str]:
    """搜索举报。返回 ``(reports, cleaned_query)``。"""
    settings = get_settings()
    page_size = page_size or settings.page_size

    backend = get_search_backend()
    ids, cleaned = await backend.search_report_ids(db, q, page_size)

    if not ids:
        like_pattern = f"%{cleaned or q}%"
        stmt = (
            select(Report)
            .join(Book, Book.id == Report.book_id)
            .options(selectinload(Report.book), selectinload(Report.evidences))
            .where(
                or_(
                    Book.title.ilike(like_pattern),
                    Book.author.ilike(like_pattern),
                    Report.description.ilike(like_pattern),
                )
            )
            .order_by(Report.created_at.desc())
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return list(result.scalars().unique().all()), cleaned or q

    stmt = (
        select(Report)
        .where(Report.id.in_(ids))
        .options(selectinload(Report.book), selectinload(Report.evidences))
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all()), cleaned

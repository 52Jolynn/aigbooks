"""书籍路由：最新举报 + 单书详情。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_session
from app.models import Book, Report
from app.schemas import BookDetailOut, RecentReportsOut, ReportOut

router = APIRouter()


@router.get("/books/recent", response_model=RecentReportsOut)
async def get_recent_reports(
    db: AsyncSession = Depends(get_session),
) -> RecentReportsOut:
    """最新 N 条举报（按 created_at DESC）。"""
    settings = get_settings()
    stmt = (
        select(Report)
        .options(
            selectinload(Report.evidences),  # type: ignore[attr-defined]
            selectinload(Report.book),  # type: ignore[attr-defined]
        )
        .order_by(Report.created_at.desc())
        .limit(settings.page_size)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().unique().all())
    return RecentReportsOut(
        reports=[ReportOut.model_validate(r) for r in reports],
        total=len(reports),
    )


@router.get("/books/{isbn}", response_model=BookDetailOut)
async def get_book_detail(
    isbn: str,
    db: AsyncSession = Depends(get_session),
) -> BookDetailOut:
    """单书详情 + 全部举报（按 created_at DESC）。"""
    stmt = (
        select(Book)
        .where(Book.isbn == isbn)
        .options(
            selectinload(Book.reports).selectinload(  # type: ignore[attr-defined]
                Report.evidences  # type: ignore[attr-defined]
            )
        )
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": "书籍不存在"})
    book.reports.sort(key=lambda r: r.created_at, reverse=True)  # type: ignore[attr-defined]  # noqa: E501
    return BookDetailOut.model_validate(book)

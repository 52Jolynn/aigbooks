"""搜索路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import ReportOut, SearchResultOut
from app.search import search_reports

router = APIRouter()


@router.get("/search", response_model=SearchResultOut)
async def search_endpoint(
    q: str,
    db: AsyncSession = Depends(get_session),
) -> SearchResultOut:
    """全文搜索举报（PG websearch_to_tsquery + ILIKE 回退）。"""
    reports, cleaned = await search_reports(db, q)
    return SearchResultOut(
        reports=[ReportOut.model_validate(r) for r in reports],
        total=len(reports),
        query=cleaned,
    )

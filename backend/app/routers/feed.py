"""RSS Feed 路由。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from feedgen.feed import FeedGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_session
from app.models import Report

router = APIRouter()


def _normalize_site_url(base_url: str) -> str:
    """强制 HTTPS。"""
    if base_url.startswith("http://"):
        return "https://" + base_url[len("http://") :]
    return base_url


@router.get("/feed/reports.rss", response_class=Response)
async def get_feed_reports(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """RSS 2.0：最新 N 条举报。"""
    settings = get_settings()
    stmt = (
        select(Report)
        .options(selectinload(Report.identifier))  # type: ignore[attr-defined]
        .order_by(Report.created_at.desc())
        .limit(settings.page_size)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().unique().all())

    base_url = str(request.base_url).rstrip("/")
    site_url = _normalize_site_url(base_url)

    fe = FeedGenerator()
    fe.id(site_url)
    fe.title("AIGBooks — Latest Reports")
    fe.link(href=site_url, rel="alternate")
    fe.description("An anonymous reader's dossier of AI-generated books.")
    fe.language("zh-CN")
    fe.updated(datetime.now(timezone.utc))

    for r in reports:
        item = fe.add_entry()
        target = r.identifier  # type: ignore[attr-defined]
        item.id(f"report-{r.id}")
        item.title(f"[{target.type}:{target.identifier}] {target.title} — {target.author}")
        item.link(href=f"{site_url}/identifiers/{target.type}/{target.identifier}")
        item.guid(f"report-{r.id}", permalink=False)
        pub = r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)
        item.published(pub.astimezone(timezone.utc))
        item.description(r.description)

    rss_bytes = fe.rss_str(pretty=True)
    return Response(
        content=rss_bytes,
        media_type="application/rss+xml; charset=utf-8",
    )

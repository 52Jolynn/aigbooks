"""举报限流：按 (ip + fingerprint) 时间窗口计数。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Report


async def check_report_rate_limit(db: AsyncSession, ip: str, fingerprint: str) -> None:
    """每 (ip + fingerprint) 在 ``report_rate_window`` 秒内最多 ``report_rate_limit`` 条举报。"""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.report_rate_window)
    count = await db.scalar(
        select(func.count())
        .select_from(Report)
        .where(
            Report.ip == ip,
            Report.fingerprint == fingerprint,
            Report.created_at >= cutoff,
        )
    )
    if (count or 0) >= settings.report_rate_limit:
        raise HTTPException(
            status_code=429,
            detail={"code": 429, "msg": "举报过于频繁，请稍后再试"},
            headers={"Retry-After": str(settings.report_rate_window)},
        )

"""聚合根路由：最新举报 + 单聚合根详情。"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_session
from app.db.constants import IdentifierType
from app.models import Identifier, Report
from app.schemas import IdentifierDetailOut, RecentReportsOut, ReportOut

router = APIRouter()


_TYPE_TO_REGEX: dict[str, re.Pattern[str]] = {
    IdentifierType.ISBN: re.compile(r"^(?:\d{9}[\dX]|\d{13})$"),
    IdentifierType.ISSN: re.compile(r"^\d{4}-?\d{3}[\dX]$"),
    IdentifierType.ISSN_L: re.compile(r"^\d{4}-?\d{3}[\dX]$"),
}


def _validate_identifier(type_: str, identifier: str) -> None:
    """校验 ``(type, identifier)`` 形态；不通过抛 422。"""
    if type_ not in IdentifierType.ALL:
        raise HTTPException(
            status_code=422,
            detail={"code": 422, "msg": f"不支持的 type: {type_}"},
        )
    normalized = identifier.replace("-", "").replace(" ", "")
    if not _TYPE_TO_REGEX[type_].match(normalized):
        raise HTTPException(
            status_code=422,
            detail={"code": 422, "msg": f"{type_} 格式不正确: {identifier}"},
        )


@router.get("/identifiers/recent", response_model=RecentReportsOut)
async def get_recent_reports(
    db: AsyncSession = Depends(get_session),
) -> RecentReportsOut:
    """最新 N 条举报 + DB 真实总数。total 字段语义：数据库中全部举报数量（不受 LIMIT 影响）。"""
    settings = get_settings()

    stmt = (
        select(Report)
        .options(
            selectinload(Report.evidences),  # type: ignore[attr-defined]
            selectinload(Report.identifier),  # type: ignore[attr-defined]
        )
        .order_by(Report.created_at.desc())
        .limit(settings.page_size)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().unique().all())

    total = await db.scalar(select(func.count()).select_from(Report))

    return RecentReportsOut(
        reports=[ReportOut.model_validate(r) for r in reports],
        total=total or 0,
    )


@router.get("/identifiers/{type}/{identifier}", response_model=IdentifierDetailOut)
async def get_identifier_detail(
    type: str,
    identifier: str,
    db: AsyncSession = Depends(get_session),
) -> IdentifierDetailOut:
    """单聚合根详情 + 全部举报（按 created_at DESC）。"""
    _validate_identifier(type, identifier)

    stmt = (
        select(Identifier)
        .where(Identifier.type == type, Identifier.identifier == identifier)
        .options(
            selectinload(Identifier.reports).options(  # type: ignore[attr-defined]
                selectinload(Report.identifier),  # type: ignore[attr-defined]
                selectinload(Report.evidences),  # type: ignore[attr-defined]
            )
        )
    )
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=404, detail={"code": 404, "msg": "聚合根不存在"}
        )
    target.reports.sort(  # type: ignore[attr-defined]
        key=lambda r: r.created_at, reverse=True
    )
    return IdentifierDetailOut.model_validate(target)

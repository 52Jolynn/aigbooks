"""举报路由：创建举报 + 投票。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.db.upsert import make_upsert
from app.middleware.rate_limit import check_report_rate_limit
from app.models import Evidence, Identifier, Report, Vote
from app.routers.identifiers import _validate_identifier
from app.schemas import ReportOut, VoteCreate
from app.services.storage import save_cover, save_evidence
from app.utils.client_ip import get_client_ip

router = APIRouter()


async def _reload_report(db: AsyncSession, report_id: int) -> Report:
    """以 Identifier + evidences 预加载方式重读 Report。"""
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.identifier),  # type: ignore[attr-defined]
            selectinload(Report.evidences),  # type: ignore[attr-defined]
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/reports", response_model=ReportOut, status_code=201)
async def create_report(
    request: Request,
    type: str = Form(..., min_length=1, max_length=16),
    identifier: str = Form(..., min_length=8, max_length=17),
    title: str = Form(..., min_length=1, max_length=500),
    author: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1, max_length=5000),
    fingerprint: str = Form(..., min_length=8, max_length=128),
    cover: UploadFile | None = File(None),
    evidences: list[UploadFile] | None = File(None),
    db: AsyncSession = Depends(get_session),
) -> ReportOut:
    _validate_identifier(type, identifier)

    ip = get_client_ip(request)
    await check_report_rate_limit(db, ip, fingerprint)

    cover_path: str | None = None
    if cover is not None and cover.filename:
        cover_path = await save_cover(cover, type, identifier)

    update_set: dict = {
        "title": title,
        "author": author,
        "updated_at": func.now(),
    }
    if cover_path is not None:
        update_set["cover_path"] = cover_path

    upsert_stmt = make_upsert(
        Identifier,
        [
            {
                "type": type,
                "identifier": identifier,
                "title": title,
                "author": author,
                "cover_path": cover_path,
                "updated_at": func.now(),
            }
        ],
        conflict_keys=["type", "identifier"],
        update_set=update_set,
    ).returning(Identifier.id)
    identifier_id = (await db.execute(upsert_stmt)).scalar_one()

    new_report = Report(
        identifier_id=identifier_id,
        description=description,
        ip=ip,
        fingerprint=fingerprint,
    )
    db.add(new_report)
    await db.flush()

    evidence_records: list[Evidence] = []
    if evidences:
        for ev_file in evidences:
            if not ev_file.filename:
                continue
            rel, mime, size = await save_evidence(ev_file)
            evidence_records.append(
                Evidence(
                    report_id=new_report.id,
                    file_path=rel,
                    file_kind=mime.split("/")[0],
                    mime_type=mime,
                    size_bytes=size,
                )
            )
    if evidence_records:
        db.add_all(evidence_records)

    await db.commit()
    report = await _reload_report(db, new_report.id)
    return ReportOut.model_validate(report)


@router.post("/reports/{report_id}/vote", response_model=ReportOut)
async def vote_report(
    report_id: int,
    request: Request,
    payload: VoteCreate,
    db: AsyncSession = Depends(get_session),
) -> ReportOut:
    ip = get_client_ip(request)
    fp = payload.fingerprint

    exists_count = await db.scalar(
        select(func.count()).select_from(Report).where(Report.id == report_id)
    )
    if not exists_count:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": "举报不存在"})

    upsert_stmt = make_upsert(
        Vote,
        [
            {
                "report_id": report_id,
                "ip": ip,
                "fingerprint": fp,
                "vote_type": payload.vote_type,
                "created_at": func.now(),
            }
        ],
        conflict_keys=["report_id", "ip", "fingerprint"],
        update_set={
            "vote_type": payload.vote_type,
            "created_at": func.now(),
        },
    )
    await db.execute(upsert_stmt)

    rows = (
        await db.execute(
            select(Vote.vote_type, func.count())
            .where(Vote.report_id == report_id)
            .group_by(Vote.vote_type)
        )
    ).all()
    upvote = sum(c for v, c in rows if v == 1)
    downvote = sum(c for v, c in rows if v == -1)

    await db.execute(
        update(Report).where(Report.id == report_id).values(upvote=upvote, downvote=downvote)
    )
    await db.commit()

    report = await _reload_report(db, report_id)
    return ReportOut.model_validate(report)

"""举报路由：创建举报 + 投票。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.middleware.rate_limit import check_report_rate_limit
from app.models import Book, Evidence, Report, Vote
from app.schemas import ReportOut, VoteCreate
from app.services.storage import save_cover, save_evidence
from app.utils.client_ip import get_client_ip

router = APIRouter()


async def _reload_report(db: AsyncSession, report_id: int) -> Report:
    """以 Book + evidences 预加载方式重读 Report。"""
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.book),  # type: ignore[attr-defined]
            selectinload(Report.evidences),  # type: ignore[attr-defined]
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/reports", response_model=ReportOut, status_code=201)
async def create_report(
    request: Request,
    isbn: str = Form(..., min_length=10, max_length=17),
    title: str = Form(..., min_length=1, max_length=500),
    author: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1, max_length=5000),
    fingerprint: str = Form(..., min_length=8, max_length=128),
    cover: UploadFile | None = File(None),
    evidences: list[UploadFile] | None = File(None),
    db: AsyncSession = Depends(get_session),
) -> ReportOut:
    ip = get_client_ip(request)
    await check_report_rate_limit(db, ip, fingerprint)

    cover_path: str | None = None
    if cover is not None and cover.filename:
        cover_path = await save_cover(cover, isbn)

    upsert_stmt = pg_insert(Book).values(
        isbn=isbn,
        title=title,
        author=author,
        cover_path=cover_path,
    )
    if cover_path is not None:
        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[Book.isbn],
            set_={
                "title": upsert_stmt.excluded.title,
                "author": upsert_stmt.excluded.author,
                "cover_path": upsert_stmt.excluded.cover_path,
                "updated_at": func.now(),
            },
        )
    else:
        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[Book.isbn],
            set_={
                "title": upsert_stmt.excluded.title,
                "author": upsert_stmt.excluded.author,
                "updated_at": func.now(),
            },
        )
    upsert_stmt = upsert_stmt.returning(Book.id)
    book_id = (await db.execute(upsert_stmt)).scalar_one()

    new_report = Report(
        book_id=book_id,
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

    insert_stmt = pg_insert(Vote).values(
        report_id=report_id,
        ip=ip,
        fingerprint=fp,
        vote_type=payload.vote_type,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[Vote.report_id, Vote.ip, Vote.fingerprint],
        set_={"vote_type": insert_stmt.excluded.vote_type, "created_at": func.now()},
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

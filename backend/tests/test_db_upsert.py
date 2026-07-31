"""UPSERT 跨方言集成测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.upsert import make_upsert
from app.models import Book, Vote


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_book_upsert_inserts_new(db_session):
    now = _now()
    stmt = make_upsert(
        Book,
        [{"isbn": "9787000000001", "title": "A", "author": "X", "updated_at": now}],
        conflict_keys=["isbn"],
        update_set={"title": "A", "author": "X", "updated_at": now},
    ).returning(Book.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    await db_session.commit()

    book = (await db_session.execute(select(Book).where(Book.id == bid))).scalar_one()
    assert book.isbn == "9787000000001"
    assert book.title == "A"


@pytest.mark.asyncio
async def test_book_upsert_updates_existing(db_session):
    now = _now()
    stmt = make_upsert(
        Book,
        [{"isbn": "9787000000002", "title": "A", "author": "X", "updated_at": now}],
        conflict_keys=["isbn"],
        update_set={"title": "A", "author": "X", "updated_at": now},
    ).returning(Book.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    await db_session.commit()

    stmt = make_upsert(
        Book,
        [
            {
                "isbn": "9787000000002",
                "title": "B",
                "author": "Y",
                "cover_path": None,
                "updated_at": now,
            }
        ],
        conflict_keys=["isbn"],
        update_set={"title": "B", "author": "Y", "updated_at": now},
    )
    await db_session.execute(stmt)
    await db_session.commit()

    book = (await db_session.execute(select(Book).where(Book.id == bid))).scalar_one()
    assert book.title == "B"
    assert book.author == "Y"


@pytest.mark.asyncio
async def test_vote_upsert_replaces_vote_type(db_session, test_db_url):
    from app.models import Report

    now = _now()
    stmt = make_upsert(
        Book,
        [{"isbn": "9787000000003", "title": "T", "author": "A", "updated_at": now}],
        conflict_keys=["isbn"],
        update_set={"title": "T", "author": "A", "updated_at": now},
    ).returning(Book.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    db_session.add(Report(book_id=bid, description="d", ip="127.0.0.1", fingerprint="fp-abc"))
    await db_session.commit()

    rid = (
        await db_session.execute(select(Report).where(Report.book_id == bid))
    ).scalars().one().id

    for vt in (1, 1):
        up = make_upsert(
            Vote,
            [
                {
                    "report_id": rid,
                    "ip": "127.0.0.1",
                    "fingerprint": "fp-abc",
                    "vote_type": vt,
                    "created_at": now,
                }
            ],
            conflict_keys=["report_id", "ip", "fingerprint"],
            update_set={"vote_type": vt, "created_at": now},
        )
        await db_session.execute(up)
        await db_session.commit()

    votes = (
        await db_session.execute(select(Vote).where(Vote.report_id == rid))
    ).scalars().all()
    assert len(votes) == 1
    assert votes[0].vote_type == 1

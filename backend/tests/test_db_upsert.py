"""UPSERT 跨方言集成测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.upsert import make_upsert
from app.models import Identifier, Vote


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_identifier_upsert_inserts_new(db_session):
    now = _now()
    stmt = make_upsert(
        Identifier,
        [
            {
                "type": "isbn",
                "identifier": "9787000000001",
                "title": "A",
                "author": "X",
                "updated_at": now,
            }
        ],
        conflict_keys=["type", "identifier"],
        update_set={"title": "A", "author": "X", "updated_at": now},
    ).returning(Identifier.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    await db_session.commit()

    target = (
        await db_session.execute(select(Identifier).where(Identifier.id == bid))
    ).scalar_one()
    assert target.type == "isbn"
    assert target.identifier == "9787000000001"
    assert target.title == "A"


@pytest.mark.asyncio
async def test_identifier_upsert_updates_existing(db_session):
    now = _now()
    stmt = make_upsert(
        Identifier,
        [
            {
                "type": "isbn",
                "identifier": "9787000000002",
                "title": "A",
                "author": "X",
                "updated_at": now,
            }
        ],
        conflict_keys=["type", "identifier"],
        update_set={"title": "A", "author": "X", "updated_at": now},
    ).returning(Identifier.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    await db_session.commit()

    stmt = make_upsert(
        Identifier,
        [
            {
                "type": "isbn",
                "identifier": "9787000000002",
                "title": "B",
                "author": "Y",
                "cover_path": None,
                "updated_at": now,
            }
        ],
        conflict_keys=["type", "identifier"],
        update_set={"title": "B", "author": "Y", "updated_at": now},
    )
    await db_session.execute(stmt)
    await db_session.commit()

    target = (
        await db_session.execute(select(Identifier).where(Identifier.id == bid))
    ).scalar_one()
    assert target.title == "B"
    assert target.author == "Y"


@pytest.mark.asyncio
async def test_identifier_upsert_isolates_across_types(db_session):
    """同 identifier、不同 type 应共存（联合唯一）。"""
    now = _now()
    for t in ("isbn", "issn"):
        stmt = make_upsert(
            Identifier,
            [
                {
                    "type": t,
                    "identifier": "1003-7055",
                    "title": f"T-{t}",
                    "author": "A",
                    "updated_at": now,
                }
            ],
            conflict_keys=["type", "identifier"],
            update_set={"title": f"T-{t}", "author": "A", "updated_at": now},
        ).returning(Identifier.id)
        await db_session.execute(stmt)
    await db_session.commit()

    rows = (
        await db_session.execute(
            select(Identifier).where(Identifier.identifier == "1003-7055")
        )
    ).scalars().all()
    assert len(rows) == 2
    types = {r.type for r in rows}
    assert types == {"isbn", "issn"}


@pytest.mark.asyncio
async def test_identifier_unique_constraint_enforced(db_session):
    """直插两次同 (type, identifier) 必须抛 IntegrityError。"""
    from app.models import Identifier as Id

    now = _now()
    db_session.add(
        Id(
            type="issn",
            identifier="1003-9999",
            title="T",
            author="A",
            updated_at=now,
        )
    )
    await db_session.commit()

    db_session.add(
        Id(
            type="issn",
            identifier="1003-9999",
            title="T",
            author="A",
            updated_at=now,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_vote_upsert_replaces_vote_type(db_session, test_db_url):
    from app.models import Report

    now = _now()
    stmt = make_upsert(
        Identifier,
        [
            {
                "type": "isbn",
                "identifier": "9787000000003",
                "title": "T",
                "author": "A",
                "updated_at": now,
            }
        ],
        conflict_keys=["type", "identifier"],
        update_set={"title": "T", "author": "A", "updated_at": now},
    ).returning(Identifier.id)
    bid = (await db_session.execute(stmt)).scalar_one()
    db_session.add(
        Report(
            identifier_id=bid,
            description="d",
            ip="127.0.0.1",
            fingerprint="fp-abc",
        )
    )
    await db_session.commit()

    rid = (
        await db_session.execute(select(Report).where(Report.identifier_id == bid))
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

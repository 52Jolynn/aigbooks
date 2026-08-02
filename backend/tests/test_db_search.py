"""全文检索方言集成测试（SQLite FTS5；PG / MySQL 需各 DB 实例）。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.db.search import get_search_backend, reset_search_backend
from app.models import Identifier, Report


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_sqlite_search_chinese_keyword(db_session):
    target = Identifier(
        type="isbn",
        identifier="9787000000011",
        title="AI换脸视频生成教程",
        author="张三",
        updated_at=_now(),
    )
    db_session.add(target)
    await db_session.flush()
    db_session.add(
        Report(
            identifier_id=target.id,
            description="这是一个深度伪造视频案例",
            ip="127.0.0.1",
            fingerprint="fp-search-1",
            created_at=_now(),
        )
    )
    db_session.add(
        Report(
            identifier_id=target.id,
            description="另一条无关的描述",
            ip="127.0.0.1",
            fingerprint="fp-search-2",
            created_at=_now(),
        )
    )
    await db_session.commit()

    reset_search_backend()
    backend = get_search_backend()
    ids, cleaned = await backend.search_report_ids(db_session, "换脸", 20)
    assert cleaned == "换脸"
    assert len(ids) >= 1

    from app.search import search_reports

    reports, _ = await search_reports(db_session, "换脸", 20)
    assert any(r.description == "这是一个深度伪造视频案例" for r in reports)


@pytest.mark.asyncio
async def test_sqlite_search_empty_query(db_session):
    target = Identifier(
        type="isbn",
        identifier="9787000000012",
        title="T",
        author="A",
        updated_at=_now(),
    )
    db_session.add(target)
    await db_session.flush()
    db_session.add(
        Report(
            identifier_id=target.id,
            description="d",
            ip="127.0.0.1",
            fingerprint="fp-empty",
            created_at=_now(),
        )
    )
    await db_session.commit()

    reset_search_backend()
    backend = get_search_backend()
    ids, cleaned = await backend.search_report_ids(db_session, "", 20)
    assert ids == []
    assert cleaned == ""


@pytest.mark.asyncio
async def test_sqlite_search_special_chars_only(db_session):
    target = Identifier(
        type="isbn",
        identifier="9787000000013",
        title="T",
        author="A",
        updated_at=_now(),
    )
    db_session.add(target)
    await db_session.flush()
    db_session.add(
        Report(
            identifier_id=target.id,
            description="d",
            ip="127.0.0.1",
            fingerprint="fp-special",
            created_at=_now(),
        )
    )
    await db_session.commit()

    reset_search_backend()
    from app.search import search_reports

    reports, _ = await search_reports(db_session, ":()&|*", 20)
    assert isinstance(reports, list)


@pytest.mark.asyncio
async def test_search_text_populated_by_event_listener(db_session):
    target = Identifier(
        type="isbn",
        identifier="9787000000099",
        title="深度伪造案例",
        author="李四",
        updated_at=_now(),
    )
    db_session.add(target)
    await db_session.flush()
    assert "深度" in target.search_text
    assert "伪造" in target.search_text
    assert "李四" in target.search_text

    report = Report(
        identifier_id=target.id,
        description="深度伪造视频示例",
        ip="127.0.0.1",
        fingerprint="fp-st-1",
        created_at=_now(),
    )
    db_session.add(report)
    await db_session.flush()
    assert "深度" in report.search_text
    assert "伪造" in report.search_text

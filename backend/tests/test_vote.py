"""投票 API 测试（需要 PostgreSQL）。"""

import os

import pytest

pytestmark = pytest.mark.asyncio

SKIP_REASON = "需要 PostgreSQL"


@pytest.fixture(autouse=True)
def require_pg():
    if not os.environ.get("AIGBOOKS_TEST_DATABASE_URL"):
        pytest.skip(SKIP_REASON)


async def test_vote_upsert_same_direction(client, db_session):
    """同方向再次投票应保持（澄清决策 §2.2.4：覆盖旧投票）。"""
    # 先创建一个 report
    isbn = "9787000000999"
    fp = "vote-test-fp-12345"
    r1 = await client.post(
        "/api/reports",
        data={
            "isbn": isbn,
            "title": "Vote Test",
            "author": "Tester",
            "description": "Test description for voting.",
            "fingerprint": fp,
        },
    )
    assert r1.status_code == 201
    report_id = r1.json()["id"]

    # 第一次投票 up
    v1 = await client.post(
        f"/api/reports/{report_id}/vote",
        json={"vote_type": 1, "fingerprint": fp},
    )
    assert v1.status_code == 200
    assert v1.json()["upvote"] == 1

    # 第二次投票 up（同方向）
    v2 = await client.post(
        f"/api/reports/{report_id}/vote",
        json={"vote_type": 1, "fingerprint": fp},
    )
    assert v2.status_code == 200
    assert v2.json()["upvote"] == 1  # 仍然 1，不是 2


async def test_vote_switch_direction(client, db_session):
    """反方向投票应切换。"""
    isbn = "9787000000998"
    fp = "vote-switch-fp-12345"
    r1 = await client.post(
        "/api/reports",
        data={
            "isbn": isbn,
            "title": "Switch Test",
            "author": "Tester",
            "description": "Test description for direction switch.",
            "fingerprint": fp,
        },
    )
    report_id = r1.json()["id"]

    await client.post(
        f"/api/reports/{report_id}/vote",
        json={"vote_type": 1, "fingerprint": fp},
    )
    v2 = await client.post(
        f"/api/reports/{report_id}/vote",
        json={"vote_type": -1, "fingerprint": fp},
    )
    assert v2.json()["upvote"] == 0
    assert v2.json()["downvote"] == 1

"""书籍 API 测试。"""

import pytest

pytestmark = pytest.mark.asyncio


async def test_recent_reports_empty(client):
    r = await client.get("/api/books/recent")
    assert r.status_code == 200
    assert r.json() == {"reports": [], "total": 0}


async def test_book_detail_not_found(client):
    r = await client.get("/api/books/0000000000")
    assert r.status_code == 404

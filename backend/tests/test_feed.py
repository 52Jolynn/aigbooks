"""RSS 输出格式测试。"""

import pytest

pytestmark = pytest.mark.asyncio


async def test_feed_endpoint_empty(client):
    r = await client.get("/api/feed/reports.rss")
    assert r.status_code == 200
    assert "application/rss+xml" in r.headers["content-type"]
    assert b"<rss" in r.content

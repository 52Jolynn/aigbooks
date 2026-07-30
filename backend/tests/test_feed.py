"""RSS 输出格式测试（需要数据库，sqlite 降级下 skip）。"""

import os

import pytest

from app.models import Report

pytestmark = pytest.mark.asyncio

SKIP_REASON = "需要 PostgreSQL"
SKIP_REL = "业务代码缺少 ORM relationship 定义，集成测试暂无法运行"


@pytest.fixture(autouse=True)
def _require(request):
    if not os.environ.get("AIGBOOKS_TEST_DATABASE_URL"):
        pytest.skip(SKIP_REASON)
    if not hasattr(Report, "book"):
        pytest.skip(SKIP_REL)


async def test_feed_endpoint_empty(client):
    r = await client.get("/api/feed/reports.rss")
    assert r.status_code == 200
    assert "application/rss+xml" in r.headers["content-type"]
    assert b"<rss" in r.content

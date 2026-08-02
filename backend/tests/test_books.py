"""聚合根 API 测试。"""

import pytest

pytestmark = pytest.mark.asyncio


async def test_recent_reports_empty(client):
    r = await client.get("/api/identifiers/recent")
    assert r.status_code == 200
    assert r.json() == {"reports": [], "total": 0}


async def test_identifier_detail_not_found(client):
    r = await client.get("/api/identifiers/isbn/0000000000000")
    assert r.status_code == 404


async def test_identifier_detail_invalid_type(client):
    r = await client.get("/api/identifiers/doi/10.1000")
    assert r.status_code == 422


async def test_identifier_detail_invalid_isbn(client):
    r = await client.get("/api/identifiers/isbn/not-a-isbn")
    assert r.status_code == 422


async def test_identifier_detail_invalid_issn(client):
    r = await client.get("/api/identifiers/issn/12345")
    assert r.status_code == 422

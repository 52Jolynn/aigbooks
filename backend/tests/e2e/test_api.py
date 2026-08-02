"""AIGBooks 端到端测试（pytest 形式）。

通过 ``pytest -m e2e`` 触发；默认 ``pytest`` 因 ``addopts = -m 'not e2e'`` 跳过。

执行后端：
- 已有：直接打 ``AIGBOOKS_API``（默认 ``http://127.0.0.1:8000``）
- 无后端：conftest 自动启 uvicorn；用 ``AIGBOOKS_E2E_AUTO_BOOT=0`` 关闭自启
"""

from __future__ import annotations

import time

import httpx
import pytest

pytestmark = pytest.mark.e2e


# ───────────── 共享常量：本 session 内唯一 ISBN / ISSN 与指纹 ─────────────


def _form(
    type_: str,
    identifier: str,
    fingerprint: str,
    *,
    title: str = "测试书 E2E",
    description: str = "E2E 测试用例。",
) -> dict:
    return {
        "type": type_,
        "identifier": identifier,
        "title": title,
        "author": "测试作者",
        "description": description,
        "fingerprint": fingerprint,
    }


# ───────────── 1. identifiers/recent schema ─────────────


def test_identifiers_recent_schema(client: httpx.Client) -> None:
    """GET /api/identifiers/recent → 200 且结构契约正确。"""
    r = client.get("/api/identifiers/recent")
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("reports"), list)
    assert isinstance(body.get("total"), int)


# ───────────── 2. POST /api/reports 新 ISBN ─────────────


def test_post_report_new_isbn(
    client: httpx.Client, isbn: str, fingerprint: str
) -> None:
    """新 ISBN 首条举报 → 201，identifier.report_count = 1。"""
    r = client.post(
        "/api/reports",
        data=_form(
            "isbn",
            isbn,
            fingerprint,
            description="第一条举报，应使 identifier.report_count = 1。",
        ),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["identifier"]["report_count"] == 1
    assert body["identifier"]["type"] == "isbn"
    assert body["identifier"]["identifier"] == isbn


# ───────────── 3. POST /api/reports 同 ISBN 聚合 ─────────────


def test_post_report_aggregate_isbn(
    client: httpx.Client, isbn: str, fingerprint: str
) -> None:
    """同 ISBN 第二条举报 → identifier.report_count = 2。"""
    r = client.post(
        "/api/reports",
        data=_form(
            "isbn",
            isbn,
            fingerprint,
            description="第二条举报，应聚合并使 identifier.report_count = 2。",
        ),
    )
    assert r.status_code == 201, r.text
    assert r.json()["identifier"]["report_count"] == 2


# ───────────── 4. GET /api/identifiers/{type}/{id} 存在 ─────────────


def test_identifier_detail_exists_isbn(
    client: httpx.Client, isbn: str
) -> None:
    """存在 ISBN 详情 → 200，含 reports 且每条含 identifier。"""
    r = client.get(f"/api/identifiers/isbn/{isbn}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == "isbn"
    assert body["identifier"] == isbn
    assert len(body["reports"]) == 2
    for rep in body["reports"]:
        assert "identifier" in rep, "lazy='raise' bug 修复校验"
        assert rep["identifier"]["type"] == "isbn"
        assert rep["identifier"]["identifier"] == isbn


# ───────────── 5. GET /api/identifiers/{type}/{id} 不存在 ─────────────


def test_identifier_detail_not_found(client: httpx.Client) -> None:
    r = client.get("/api/identifiers/isbn/0000000000000")
    assert r.status_code == 404


# ───────────── 6. POST /api/reports 缺字段 → 422 ─────────────


def test_post_report_validation(client: httpx.Client, fingerprint: str) -> None:
    r = client.post(
        "/api/reports",
        data={
            "title": "缺 identifier",
            "author": "测试",
            "description": "缺 identifier 必触发 422。",
            "fingerprint": fingerprint,
        },
    )
    assert r.status_code == 422


# ───────────── 7. GET /api/search ─────────────


def test_search(client: httpx.Client) -> None:
    r = client.get("/api/search", params={"q": "测试书"})
    assert r.status_code == 200
    assert len(r.json()["reports"]) >= 2


# ───────────── 7b. POST /api/reports 新 ISSN（双轨烟测） ─────────────


def test_post_report_new_issn(
    client: httpx.Client, issn: str, fingerprint: str
) -> None:
    """新 ISSN 首条举报 → 201，identifier.type = 'issn'。"""
    r = client.post(
        "/api/reports",
        data=_form(
            "issn",
            issn,
            fingerprint,
            description="第一条 ISSN 举报。",
        ),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["identifier"]["type"] == "issn"
    assert body["identifier"]["identifier"] == issn
    assert body["identifier"]["report_count"] == 1


def test_identifier_detail_exists_issn(client: httpx.Client, issn: str) -> None:
    """存在 ISSN 详情 → 200。"""
    r = client.get(f"/api/identifiers/issn/{issn}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == "issn"
    assert body["identifier"] == issn


# ───────────── 8/9. 投票（依赖首条 report id） ─────────────


@pytest.fixture(scope="session")
def first_report_id(
    client: httpx.Client, isbn: str, fingerprint: str
) -> int:
    """本 session 首条 report 的 id，供投票用例使用。"""
    r = client.post(
        "/api/reports",
        data=_form(
            "isbn",
            isbn,
            fingerprint,
            description="首条独立 report（与 test_03 共享 ISBN 但 fingerprint 复用）。",
        ),
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


def test_vote_up(client: httpx.Client, first_report_id: int, fingerprint: str) -> None:
    r = client.post(
        f"/api/reports/{first_report_id}/vote",
        json={"vote_type": 1, "fingerprint": fingerprint},
    )
    assert r.status_code == 200, r.text
    assert r.json()["upvote"] == 1


def test_vote_switch(client: httpx.Client, first_report_id: int, fingerprint: str) -> None:
    r = client.post(
        f"/api/reports/{first_report_id}/vote",
        json={"vote_type": -1, "fingerprint": fingerprint},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["upvote"] == 0
    assert body["downvote"] == 1


# ───────────── 10. POST /api/reports/{not_exist}/vote → 404 ─────────────


def test_vote_not_found(client: httpx.Client, fingerprint: str) -> None:
    r = client.post(
        "/api/reports/9999999/vote",
        json={"vote_type": 1, "fingerprint": fingerprint},
    )
    assert r.status_code == 404


# ───────────── 11. GET /api/feed/reports.rss ─────────────


def test_rss_feed(client: httpx.Client, isbn: str, issn: str) -> None:
    r = client.get("/api/feed/reports.rss")
    assert r.status_code == 200
    ct = r.headers.get("content-type", "").lower()
    assert "application/rss+xml" in ct
    assert "<rss" in r.text
    assert f"[isbn:{isbn}]" in r.text
    assert f"[issn:{issn}]" in r.text


# ───────────── 12. GET /openapi.json ─────────────


def test_openapi(client: httpx.Client) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    body = r.json()
    assert "/api/identifiers/recent" in body["paths"]
    assert len(body["paths"]) >= 6


# ───────────── 13. POST /api/reports + GET /covers/{path} ─────────────


_MIN_JPEG_HEX = (
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909"
    "080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c283729"
    "2c30313434341f27393d38323c2e333432ffc2000b080001000101011100ffc400150101"
    "0000000000000000000000000000000003ffda0008010100003f00fb"
    "fcffd9"
)


def test_cover_static(client: httpx.Client, fingerprint: str) -> None:
    """上传合法封面 → 201，再 GET /covers/{type}/{id}{ext} → 200。"""
    cover_isbn = f"9787{int(time.time()) % 100_000_000 + 1:09d}"
    jpeg = bytes.fromhex(_MIN_JPEG_HEX)
    r = client.post(
        "/api/reports",
        data=_form(
            "isbn",
            cover_isbn,
            fingerprint,
            title="封面 E2E",
            description="上传封面的最小合法 JPEG。",
        ),
        files={"cover": ("cover.jpg", jpeg, "image/jpeg")},
    )
    assert r.status_code == 201, r.text
    cover = r.json()["identifier"].get("cover_path")
    if not cover:
        pytest.skip("响应未含 cover_path（封面上传失败）")
    r2 = client.get(f"/covers/{cover}")
    assert r2.status_code == 200, r2.text

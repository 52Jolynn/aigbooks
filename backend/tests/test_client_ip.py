"""客户端 IP 获取工具测试（纯逻辑，不需 DB）。"""

from typing import Any


def _make_fake_request(headers: dict | None = None, host: str = "127.0.0.1") -> Any:
    """构造一个 duck-typed 的伪 Request 对象（仅提供 headers + client）。"""
    req: Any = type("FakeRequest", (), {})()
    req.headers = headers or {}
    req.client = type("Client", (), {"host": host})()
    return req


def test_get_client_ip_from_xff():
    from app.utils.client_ip import get_client_ip

    req = _make_fake_request(headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"})
    assert get_client_ip(req) == "1.2.3.4"


def test_get_client_ip_fallback_to_host():
    from app.utils.client_ip import get_client_ip

    req = _make_fake_request(host="192.168.1.1")
    assert get_client_ip(req) == "192.168.1.1"


def test_get_client_ip_no_client():
    from app.utils.client_ip import get_client_ip

    req: Any = _make_fake_request()
    req.client = None
    assert get_client_ip(req) == "0.0.0.0"


def test_get_client_ip_xff_first_only():
    """多 IP 时只取第一个（最左为真实客户端）。"""
    from app.utils.client_ip import get_client_ip

    req = _make_fake_request(headers={"X-Forwarded-For": "  1.2.3.4  ,  10.0.0.1  "})
    assert get_client_ip(req) == "1.2.3.4"


def test_get_client_ip_xff_empty_falls_back():
    """XFF 为空字符串时应回退到 client.host。"""
    from app.utils.client_ip import get_client_ip

    req = _make_fake_request(headers={"X-Forwarded-For": ""}, host="10.0.0.5")
    # empty string 是 falsy，所以会走 fallback 分支
    assert get_client_ip(req) == "10.0.0.5"

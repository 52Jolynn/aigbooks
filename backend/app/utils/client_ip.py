"""客户端 IP 解析工具。"""

from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """从 X-Forwarded-For 或 request.client.host 取真实 IP。"""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "0.0.0.0"

"""AIGBooks E2E 测试 fixtures。

自动启动一个 uvicorn 子进程（除非已运行），并 yield ``base_url``；
yield 后自动终止。环境变量：

- ``AIGBOOKS_API``: 期望的 base URL（默认 ``http://127.0.0.1:8000``）
- ``AIGBOOKS_E2E_PORT``: 端口（默认 8000）
- ``AIGBOOKS_E2E_AUTO_BOOT=0``: 禁用自动启动；后端不可用则直接 fail
"""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

DEFAULT_PORT = int(os.environ.get("AIGBOOKS_E2E_PORT", "8000"))
DEFAULT_BASE = os.environ.get("AIGBOOKS_API", f"http://127.0.0.1:{DEFAULT_PORT}")
USER_AGENT = "aigbooks-e2e-pytest/1.0"


def _probe(url: str) -> bool:
    try:
        r = httpx.get(f"{url.rstrip('/')}/api/identifiers/recent", timeout=1.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """E2E 测试用的 base URL；按需自动启 uvicorn。"""
    auto_boot = os.environ.get("AIGBOOKS_E2E_AUTO_BOOT", "1") != "0"
    url = DEFAULT_BASE.rstrip("/")

    if _probe(url):
        yield url
        return

    if not auto_boot:
        pytest.fail(f"后端不可用: {url}（已通过 AIGBOOKS_E2E_AUTO_BOOT=0 禁用自动启动）")

    backend = Path(__file__).resolve().parents[2]
    if not (backend / "app").is_dir():
        pytest.fail(f"找不到 backend 目录: {backend}")

    log_path = Path("/tmp/aigbooks-e2e-pytest.log")
    log_path.unlink(missing_ok=True)
    log_f = log_path.open("w", encoding="utf-8")

    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(DEFAULT_PORT),
        ],
        cwd=str(backend),
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )

    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            if _probe(url):
                break
            if proc.poll() is not None:
                pytest.fail(f"uvicorn 提前退出，详见 {log_path}")
            time.sleep(0.3)
        else:
            pytest.fail(f"等待 {url} 就绪超时，详见 {log_path}")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_f.close()


@pytest.fixture(scope="session")
def client(base_url: str) -> Iterator[httpx.Client]:
    """复用连接的 httpx.Client（session-scope，串行测试安全）。"""
    with httpx.Client(
        base_url=base_url,
        timeout=10.0,
        headers={"User-Agent": USER_AGENT},
    ) as c:
        yield c


@pytest.fixture(scope="session")
def fingerprint() -> str:
    """一次 e2e 运行共享一个 fingerprint，便于聚合到同一条数据。"""
    return f"e2e-pytest-{uuid.uuid4()}"


@pytest.fixture(scope="session")
def isbn() -> str:
    """一次 e2e 运行共享一个 ISBN。"""
    return f"9787{int(time.time()) % 100_000_000:09d}"


@pytest.fixture(scope="session")
def issn() -> str:
    """一次 e2e 运行共享一个 ISSN。"""
    return f"1003-{int(time.time()) % 1000:04d}"

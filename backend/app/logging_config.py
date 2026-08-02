"""集中式日志配置：标准库 ``logging`` + ``TimedRotatingFileHandler``。

设计要点：
- 按天滚动（``when='midnight'``），文件名后缀 ``%Y-%m-%d``
- 同时输出到 stderr 与文件，便于 ``docker logs`` / ``journalctl`` 抓取
- 通过 ``propagate=True`` 自动接管 uvicorn / sqlalchemy / jieba 等所有 stdlib logger
- ``setup_logging()`` 必须先于 ``uvicorn.run``/``create_app`` 调用，避免 uvicorn 默认
  ``configure_logging`` 覆盖
- 单进程单线程下文件写入安全；多 worker 共享同一日志文件需外置 ``-log-config`` 或
  显式锁（``ConcurrentRotatingFileHandler``），不在本模块范围
"""

from __future__ import annotations

import contextlib
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config import Settings

_FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
)
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _build_file_handler(log_dir: Path, retention_days: int) -> TimedRotatingFileHandler:
    """按天滚动文件 handler。"""
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = TimedRotatingFileHandler(
        filename=log_dir / "aigbooks.log",
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        utc=False,
        delay=False,
    )
    handler.suffix = "%Y-%m-%d"
    return handler


def setup_logging(settings: Settings) -> None:
    """初始化全局日志。幂等：重复调用仅保留最后一组 handler。"""
    root = logging.getLogger()

    for h in list(root.handlers):
        root.removeHandler(h)
        with contextlib.suppress(Exception):
            h.close()

    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    file_handler = _build_file_handler(settings.log_dir, settings.log_retention_days)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if settings.log_to_console:
        stream_handler = logging.StreamHandler(stream=sys.stderr)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    root.setLevel(settings.log_level.upper())

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True

    logging.captureWarnings(True)

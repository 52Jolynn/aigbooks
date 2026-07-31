"""通用文本工具：搜索关键词清洗、空白归一化。"""

from __future__ import annotations

import re

_SPECIAL_CHARS = re.compile(r"[():&|!*\"'<>\-]")
_WHITESPACE = re.compile(r"\s+")


def sanitize_query(q: str) -> str:
    """去除全文检索特殊字符与多余空白。

    适用于 PG tsquery / SQLite FTS5 / MySQL FULLTEXT 通用场景。
    """
    q = _SPECIAL_CHARS.sub(" ", q).strip()
    q = _WHITESPACE.sub(" ", q)
    return q

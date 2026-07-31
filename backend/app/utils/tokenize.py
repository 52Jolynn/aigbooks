"""中文分词包装：基于 jieba，提供进程级预热 + 同步缓存。"""

from __future__ import annotations

import threading
from functools import lru_cache

import jieba

_lock = threading.Lock()
_warmed = False


def warmup() -> None:
    """进程级预热：触发主词典加载；幂等。"""
    global _warmed
    with _lock:
        if _warmed:
            return
        list(jieba.cut("初始化"))
        _warmed = True


@lru_cache(maxsize=1024)
def cut_for_search(text: str) -> tuple[str, ...]:
    """搜索引擎模式分词，返回不可变 ``tuple``。"""
    return tuple(t for t in jieba.cut_for_search(text) if t.strip())


def join_tokens(tokens: tuple[str, ...] | list[str]) -> str:
    """FTS5 MATCH 表达式：token 之间用单空格分隔；尾部不带空格。"""
    return " ".join(tokens)

"""SQLite FTS5 查询辅助：把中文文本转成 ``MATCH`` 表达式。

SQLite FTS5 在 Python 中无法实现自定义 tokenizer（C 层 API），
因此本项目采用 **索引端 ``unicode61`` + 查询端 jieba** 的混合策略：

- FTS5 虚拟表用 ``tokenize='unicode61'`` 索引（按 Unicode 字符 + 小写 + 去标点）
- 查询端用 :func:`app.utils.tokenize.cut_for_search` 把用户输入切成 token
- token 之间用单空格拼接为 ``MATCH`` 表达式，召回包含任一 token 的行

该策略对中英文混合输入均有可接受的召回率，规避了 Python sqlite3 不可实现
FTS5 自定义分词器的限制。
"""

from __future__ import annotations

from app.utils.tokenize import cut_for_search, join_tokens

_FTS5_SPECIAL_CHARS = str.maketrans("", "", "():&|*\"'<>-")


def escape_fts5_query(text: str) -> str:
    """去除 FTS5 保留字符，仅保留字母数字、中文、空格。"""
    return text.translate(_FTS5_SPECIAL_CHARS)


def build_match_query(text: str) -> str:
    """构建 FTS5 ``MATCH`` 表达式。

    Args:
        text: 用户搜索输入。

    Returns:
        空格分隔的 token 串；空输入返回空串（调用方走 LIKE 回退）。
    """
    cleaned = escape_fts5_query(text).strip()
    if not cleaned:
        return ""
    tokens = cut_for_search(cleaned)
    return join_tokens(tokens)

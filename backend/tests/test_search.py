"""FTS 输入清洗测试（纯逻辑，不需 DB）。"""

from app.utils.text import sanitize_query


def test_sanitize_query_removes_special_chars():
    assert sanitize_query("hello:&|!world") == "hello world"


def test_sanitize_query_strips_whitespace():
    assert sanitize_query("  hello world  ") == "hello world"


def test_sanitize_query_preserves_chinese():
    assert sanitize_query("中文测试") == "中文测试"


def test_sanitize_query_handles_empty():
    assert sanitize_query("") == ""
    assert sanitize_query("   ") == ""


def test_sanitize_query_handles_only_specials():
    assert sanitize_query(":&|!()*") == ""

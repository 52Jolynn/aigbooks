"""方言无关的 ORM 类型：TypeDecorator 抽象 PG 专属类型。"""

from __future__ import annotations

import ipaddress

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.types import TypeDecorator


class TsVector(TypeDecorator):
    """全文检索向量。

    - PostgreSQL：原生 ``TSVECTOR``，由 DB 触发器维护，Python 不写入
    - SQLite / MySQL：降级为 nullable ``Text``（FTS5 影子表 / FULLTEXT 由外部机制维护）
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            return dialect.type_descriptor(TSVECTOR())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        return value

    def process_result_value(self, value, dialect):  # noqa: ANN001
        return value


class IpAddress(TypeDecorator):
    """IPv4 / IPv6 字符串地址。

    任意方言均映射为 ``String(45)``（兼容 IPv6 完整表示）；
    ORM 写入时通过 ``ipaddress.ip_address`` 校验合法性。
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        return dialect.type_descriptor(String(45))

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        ipaddress.ip_address(value)
        return value

    def process_result_value(self, value, dialect):  # noqa: ANN001
        return value

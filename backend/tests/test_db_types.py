"""TypeDecorator 单测：``TsVector`` / ``IpAddress`` bind/result 对称。"""

from __future__ import annotations

import pytest
from sqlalchemy.dialects import mysql, postgresql, sqlite

from app.db.types import IpAddress, TsVector


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_tsvector_round_trip(dialect):
    tv = TsVector()
    bind = tv.process_bind_param("hello world", dialect)
    result = tv.process_result_value(bind, dialect)
    assert bind == result == "hello world"


@pytest.mark.parametrize(
    "dialect,expected_class_name",
    [
        (postgresql.dialect(), "TSVECTOR"),
        (sqlite.dialect(), "Text"),
        (mysql.dialect(), "Text"),
    ],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_tsvector_dialect_impl(dialect, expected_class_name):
    tv = TsVector()
    impl = tv.load_dialect_impl(dialect)
    assert type(impl).__name__ == expected_class_name


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_ip_address_accepts_ipv4(dialect):
    ip = IpAddress()
    assert ip.process_bind_param("127.0.0.1", dialect) == "127.0.0.1"


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_ip_address_accepts_ipv6(dialect):
    ip = IpAddress()
    assert ip.process_bind_param("::1", dialect) == "::1"
    assert ip.process_bind_param("2001:db8::1", dialect) == "2001:db8::1"


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_ip_address_accepts_none(dialect):
    ip = IpAddress()
    assert ip.process_bind_param(None, dialect) is None


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_ip_address_rejects_invalid(dialect):
    ip = IpAddress()
    with pytest.raises(ValueError):
        ip.process_bind_param("not.an.ip", dialect)


@pytest.mark.parametrize(
    "dialect",
    [postgresql.dialect(), sqlite.dialect(), mysql.dialect()],
    ids=["postgresql", "sqlite", "mysql"],
)
def test_ip_address_impl_is_string45(dialect):
    impl = IpAddress().load_dialect_impl(dialect)
    assert type(impl).__name__ == "String"
    assert impl.length == 45

"""数据库方言常量：消除魔术字符串。

所有 dialect 名称与 URL scheme 集中在此处定义，业务代码禁止直接写字面量。
"""

from __future__ import annotations

from typing import Literal

DIALECT_POSTGRESQL: Literal["postgresql"] = "postgresql"
DIALECT_SQLITE: Literal["sqlite"] = "sqlite"
DIALECT_MYSQL: Literal["mysql"] = "mysql"

ALL_DIALECTS: tuple[Literal["postgresql", "sqlite", "mysql"], ...] = (
    DIALECT_POSTGRESQL,
    DIALECT_SQLITE,
    DIALECT_MYSQL,
)

DialectName = Literal["postgresql", "sqlite", "mysql"]

URL_SCHEME_POSTGRESQL = "postgresql+asyncpg"
URL_SCHEME_SQLITE = "sqlite+aiosqlite"
URL_SCHEME_MYSQL = "mysql+asyncmy"

URL_SCHEME_TO_DIALECT: dict[str, DialectName] = {
    URL_SCHEME_POSTGRESQL: DIALECT_POSTGRESQL,
    URL_SCHEME_SQLITE: DIALECT_SQLITE,
    URL_SCHEME_MYSQL: DIALECT_MYSQL,
}

SUPPORTED_URL_PREFIXES = ", ".join(sorted(URL_SCHEME_TO_DIALECT.keys()))


class IdentifierType:
    """聚合根标识符类型。

    业务上代表「一本书 / 一本期刊 / 一个 ISSN 链接集群」，底层存储为字符串字面量。
    扩展新类型只需新增常量 + 正则映射，**不需要** DB 迁移（String(16) 预留空间）。
    """

    ISBN: Literal["isbn"] = "isbn"
    ISSN: Literal["issn"] = "issn"
    ISSN_L: Literal["issn-l"] = "issn-l"

    ALL: tuple[Literal["isbn", "issn", "issn-l"], ...] = ("isbn", "issn", "issn-l")

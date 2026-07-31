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

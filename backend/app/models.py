"""SQLAlchemy 2.0 ORM 模型（AIGBooks 数据模型）。

四张表：books / reports / evidences / votes。

设计原则：
- 使用 SQLAlchemy 2.0 typed ``Mapped[...]`` API + ``mapped_column()``
- ``tsv_*`` 列用 ``TsVector`` TypeDecorator：PG 下为 TSVECTOR（由 DB 触发器维护），
  SQLite/MySQL 下为 Text（FULLTEXT 索引由外部机制维护）
- ``search_text`` 列存储 jieba 切词后空格拼接的字符串；
  SQLite 下被 FTS5 影子表索引；PG/MySQL 下由原生全文机制处理
- 关系用 ``relationship`` 显式声明，``lazy="raise"`` 防止隐式懒加载
  （async SQLAlchemy 不支持隐式懒加载,会抛 ``MissingGreenlet``）
- ``cascade="all, delete-orphan"`` 与 FK ``ON DELETE CASCADE`` 一致
- IP 字段统一为 ``String(45)``（兼容 IPv4/IPv6 完整表示）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db.types import TsVector
from app.utils.tokenize import cut_for_search
from app.utils.tokenize import warmup as warmup_jieba

warmup_jieba()


def _join_search_text(*parts: str | None) -> str:
    parts_list = [p for p in parts if p]
    if not parts_list:
        return ""
    tokens: set[str] = set()
    for part in parts_list:
        tokens.update(cut_for_search(part))
    return " ".join(sorted(tokens))


class Book(Base):
    """书籍聚合根（按 ISBN 唯一）。"""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    isbn: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    cover_path: Mapped[str | None] = mapped_column(Text)
    report_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    tsv_meta: Mapped[Any | None] = mapped_column(TsVector)
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    reports: Mapped[list["Report"]] = relationship(  # noqa: UP037
        "Report", back_populates="book", cascade="all, delete-orphan", lazy="raise"
    )


class Report(Base):
    """举报记录。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tsv_desc: Mapped[Any | None] = mapped_column(TsVector)
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    upvote: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    downvote: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    book: Mapped["Book"] = relationship("Book", back_populates="reports", lazy="raise")  # noqa: UP037
    evidences: Mapped[list["Evidence"]] = relationship(  # noqa: UP037
        "Evidence", back_populates="report", cascade="all, delete-orphan", lazy="raise"
    )


class Evidence(Base):
    """证据文件。"""

    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_kind: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    report: Mapped["Report"] = relationship("Report", back_populates="evidences", lazy="raise")  # noqa: UP037


class Vote(Base):
    """投票唯一性记录（一个 (report_id, ip, fingerprint) 三元组只能存在一条）。"""

    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("report_id", "ip", "fingerprint", name="uq_vote"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    vote_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


@event.listens_for(Book, "before_insert")
@event.listens_for(Book, "before_update")
def _populate_book_search_text(_mapper, _connection, target):  # noqa: ANN001
    target.search_text = _join_search_text(target.title, target.author)


@event.listens_for(Report, "before_insert")
@event.listens_for(Report, "before_update")
def _populate_report_search_text(_mapper, _connection, target):  # noqa: ANN001
    target.search_text = _join_search_text(target.description)

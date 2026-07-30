"""SQLAlchemy 2.0 ORM 模型（AIGBooks 数据模型）。

四张表：books / reports / evidences / votes。

设计原则：
- 使用 SQLAlchemy 2.0 typed ``Mapped[...]`` API + ``mapped_column()``
- ``tsv_*`` 列类型为 ``TSVECTOR``，由数据库触发器维护，Python 端不需要写入
- 关系用 ``relationship`` 显式声明，``lazy="raise"`` 防止隐式懒加载
  （async SQLAlchemy 不支持隐式懒加载,会抛 ``MissingGreenlet``）
- ``cascade="all, delete-orphan"`` 与 FK ``ON DELETE CASCADE`` 一致
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Book(Base):
    """书籍聚合根（按 ISBN 唯一）。"""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    isbn: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(Text, nullable=False)
    cover_path: Mapped[str | None] = mapped_column(Text)
    report_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    tsv_meta: Mapped[Any] = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    reports: Mapped[list["Report"]] = relationship(  # noqa: UP037
        "Report", back_populates="book", cascade="all, delete-orphan", lazy="raise"
    )


class Report(Base):
    """举报记录。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tsv_desc: Mapped[Any] = mapped_column(TSVECTOR)
    upvote: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    downvote: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    book: Mapped["Book"] = relationship("Book", back_populates="reports", lazy="raise")  # noqa: UP037
    evidences: Mapped[list["Evidence"]] = relationship(  # noqa: UP037
        "Evidence", back_populates="report", cascade="all, delete-orphan", lazy="raise"
    )


class Evidence(Base):
    """证据文件。"""

    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    vote_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

"""Pydantic v2 请求/响应模型。

设计原则：
- 响应模型统一开启 ``from_attributes=True``，从 ORM 对象自动转换
- 嵌套结构显式建模，避免依赖隐式 ORM 关系（schemas 不 import models）
- 请求模型只校验必要字段，业务规则（如 ISBN 格式）放在 router 层
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BookSummary(BaseModel):
    """用于嵌套在 ``ReportOut`` 中的书籍摘要。"""

    model_config = ConfigDict(from_attributes=True)

    isbn: str
    title: str
    author: str
    cover_path: str | None
    report_count: int


class EvidenceOut(BaseModel):
    """证据文件响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_kind: str
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime


class ReportOut(BaseModel):
    """首页 / 搜索 / 详情共用：举报 + 嵌套书籍摘要 + 证据列表。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    book: BookSummary
    description: str
    upvote: int
    downvote: int
    created_at: datetime
    evidences: list[EvidenceOut] = Field(default_factory=list)


class BookDetailOut(BookSummary):
    """书籍详情：BookSummary + 创建/更新时间 + 全部 reports 列表。"""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
    reports: list[ReportOut] = Field(default_factory=list)


class RecentReportsOut(BaseModel):
    """首页响应。"""

    reports: list[ReportOut]
    total: int


class SearchResultOut(BaseModel):
    """搜索响应。"""

    reports: list[ReportOut]
    total: int
    query: str


class VoteCreate(BaseModel):
    """投票请求体。"""

    vote_type: Literal[-1, 1]
    fingerprint: str = Field(min_length=8, max_length=128)

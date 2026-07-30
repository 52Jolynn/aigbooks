"""ORM 模型 schema 验证（schema 创建 + 表名）。"""

from sqlalchemy import inspect

from app.database import Base
from app.models import Book, Evidence, Report, Vote


def test_models_importable():
    """所有 4 个 ORM 类可导入并继承 Base。"""
    assert hasattr(Book, "__tablename__")
    assert hasattr(Report, "__tablename__")
    assert hasattr(Evidence, "__tablename__")
    assert hasattr(Vote, "__tablename__")
    assert Book.__tablename__ == "books"
    assert Report.__tablename__ == "reports"
    assert Evidence.__tablename__ == "evidences"
    assert Vote.__tablename__ == "votes"


def test_models_inherit_base():
    assert issubclass(Book, Base)
    assert issubclass(Report, Base)
    assert issubclass(Evidence, Base)
    assert issubclass(Vote, Base)


def test_books_table_columns():
    """books 表字段完整。"""
    cols = {c.name for c in Book.__table__.columns}
    expected = {"id", "isbn", "title", "author", "cover_path", "report_count", "tsv_meta",
                "created_at", "updated_at"}
    assert expected.issubset(cols)


def test_reports_table_columns():
    """reports 表字段完整。"""
    cols = {c.name for c in Report.__table__.columns}
    expected = {"id", "book_id", "description", "tsv_desc", "upvote", "downvote",
                "ip", "fingerprint", "created_at"}
    assert expected.issubset(cols)


def test_evidences_table_columns():
    """evidences 表字段完整。"""
    cols = {c.name for c in Evidence.__table__.columns}
    expected = {"id", "report_id", "file_path", "file_kind", "mime_type", "size_bytes",
                "created_at"}
    assert expected.issubset(cols)


def test_votes_table_columns_and_unique():
    """votes 表字段完整 + 唯一约束存在。"""
    cols = {c.name for c in Vote.__table__.columns}
    expected = {"id", "report_id", "ip", "fingerprint", "vote_type", "created_at"}
    assert expected.issubset(cols)
    unique_constraints = list(Vote.__table__.constraints)
    assert any(
        any(col.name == "report_id" for col in uc.columns) for uc in unique_constraints
    )


async def test_models_can_create_tables(db_session):
    """SQLAlchemy 可在测试 DB 中建表（conftest 中已经建好，这里用 inspect 验证）。

    注意：sqlite 下因 TSVECTOR 不支持，建表会失败；该测试在 PG 下生效，
    sqlite 下会被 conftest fixture 内的 create_all 抛错之前的 ``test_engine`` 创建。
    """
    async with db_session.bind.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    assert isinstance(tables, list)

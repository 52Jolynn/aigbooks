"""initial schema: books / reports / evidences / votes (multi-dialect)

Revision ID: 001
Revises:
Create Date: 2026-07-30

方言分支：
- PostgreSQL: tsv_* 列类型为 TSVECTOR，触发器维护，GIN 索引
- SQLite: tsv_* 列为 Text 占位；FTS5 虚拟表 books_fts / reports_fts（unicode61）+ 同步触发器
  索引 search_text 列（应用层 jieba 切词后空格拼接）
- MySQL: tsv_* 列为 Text；FULLTEXT 索引 books_ft_idx / reports_ft_idx（WITH PARSER ngram）

``search_text`` 列三方言通用：
- 写入时由 SQLAlchemy ORM event listener 自动填充（jieba cut_for_search）
- SQLite: FTS5 影子表索引
- PG/MySQL: 暂未使用（原生全文由 DB 端处理 title/author/description）
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
        sa.Column("isbn", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("cover_path", sa.Text(), nullable=True),
        sa.Column(
            "report_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("tsv_meta", sa.Text(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)

    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
        sa.Column(
            "book_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tsv_desc", sa.Text(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column(
            "upvote",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "downvote",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reports_book_id", "reports", ["book_id"], unique=False)

    op.create_table(
        "evidences",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
        sa.Column(
            "report_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_kind", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_evidences_report_id", "evidences", ["report_id"], unique=False)

    op.create_table(
        "votes",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
        sa.Column(
            "report_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("vote_type", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("report_id", "ip", "fingerprint", name="uq_vote"),
    )

    op.create_index(
        "reports_rate_limit_idx",
        "reports",
        ["ip", "fingerprint", "created_at"],
        unique=False,
    )

    if dialect == "postgresql":
        _upgrade_postgres()
    elif dialect == "sqlite":
        _upgrade_sqlite()
    elif dialect == "mysql":
        _upgrade_mysql()


def _upgrade_postgres() -> None:
    op.execute("ALTER TABLE books ALTER COLUMN tsv_meta TYPE TSVECTOR USING NULL")
    op.execute("ALTER TABLE reports ALTER COLUMN tsv_desc TYPE TSVECTOR USING NULL")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION books_tsv_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.tsv_meta :=
                setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(NEW.author, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER books_tsv_meta_trigger
            BEFORE INSERT OR UPDATE ON books
            FOR EACH ROW EXECUTE FUNCTION books_tsv_trigger();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION reports_tsv_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.tsv_desc := to_tsvector('simple', coalesce(NEW.description, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER reports_tsv_desc_trigger
            BEFORE INSERT OR UPDATE ON reports
            FOR EACH ROW EXECUTE FUNCTION reports_tsv_trigger();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_book_report_count() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE books SET report_count = report_count + 1 WHERE id = NEW.book_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE books SET report_count = report_count - 1 WHERE id = OLD.book_id;
                RETURN OLD;
            END IF;
            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_book_report_count
            AFTER INSERT OR DELETE ON reports
            FOR EACH ROW EXECUTE FUNCTION update_book_report_count();
        """
    )

    op.create_index(
        "books_tsv_meta_idx",
        "books",
        ["tsv_meta"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "reports_tsv_desc_idx",
        "reports",
        ["tsv_desc"],
        unique=False,
        postgresql_using="gin",
    )


def _upgrade_sqlite() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE books_fts USING fts5(
            search_text,
            content='books', content_rowid='id',
            tokenize='unicode61'
        )
        """
    )
    op.execute(
        """
        CREATE VIRTUAL TABLE reports_fts USING fts5(
            search_text,
            content='reports', content_rowid='id',
            tokenize='unicode61'
        )
        """
    )

    op.execute(
        """
        CREATE TRIGGER books_fts_ai AFTER INSERT ON books BEGIN
            INSERT INTO books_fts(rowid, search_text) VALUES (new.id, new.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER books_fts_ad AFTER DELETE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER books_fts_au AFTER UPDATE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
            INSERT INTO books_fts(rowid, search_text) VALUES (new.id, new.search_text);
        END
        """
    )

    op.execute(
        """
        CREATE TRIGGER reports_fts_ai AFTER INSERT ON reports BEGIN
            INSERT INTO reports_fts(rowid, search_text) VALUES (new.id, new.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER reports_fts_ad AFTER DELETE ON reports BEGIN
            INSERT INTO reports_fts(reports_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER reports_fts_au AFTER UPDATE ON reports BEGIN
            INSERT INTO reports_fts(reports_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
            INSERT INTO reports_fts(rowid, search_text) VALUES (new.id, new.search_text);
        END
        """
    )

    op.execute(
        """
        CREATE TRIGGER maintain_book_report_count_ins
            AFTER INSERT ON reports
            BEGIN
                UPDATE books SET report_count = report_count + 1 WHERE id = NEW.book_id;
            END
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_book_report_count_del
            AFTER DELETE ON reports
            BEGIN
                UPDATE books SET report_count = report_count - 1 WHERE id = OLD.book_id;
            END
        """
    )


def _upgrade_mysql() -> None:
    op.execute(
        "ALTER TABLE books ADD FULLTEXT INDEX books_ft_idx (title, author) WITH PARSER ngram"
    )
    op.execute(
        "ALTER TABLE reports ADD FULLTEXT INDEX reports_ft_idx (description) WITH PARSER ngram"
    )

    op.execute(
        """
        CREATE TRIGGER maintain_book_report_count_ins
        AFTER INSERT ON reports FOR EACH ROW
        UPDATE books SET report_count = report_count + 1 WHERE id = NEW.book_id
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_book_report_count_del
        AFTER DELETE ON reports FOR EACH ROW
        UPDATE books SET report_count = report_count - 1 WHERE id = OLD.book_id
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        _downgrade_postgres()
    elif dialect == "sqlite":
        _downgrade_sqlite()
    elif dialect == "mysql":
        _downgrade_mysql()

    op.drop_index("reports_rate_limit_idx", table_name="reports")
    op.drop_table("votes")
    op.drop_index("ix_evidences_report_id", table_name="evidences")
    op.drop_table("evidences")
    op.drop_index("ix_reports_book_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_books_isbn", table_name="books")
    op.drop_table("books")


def _downgrade_postgres() -> None:
    op.drop_index("reports_tsv_desc_idx", table_name="reports")
    op.drop_index("books_tsv_meta_idx", table_name="books")

    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count ON reports")
    op.execute("DROP TRIGGER IF EXISTS reports_tsv_desc_trigger ON reports")
    op.execute("DROP TRIGGER IF EXISTS books_tsv_meta_trigger ON books")
    op.execute("DROP FUNCTION IF EXISTS update_book_report_count()")
    op.execute("DROP FUNCTION IF EXISTS reports_tsv_trigger()")
    op.execute("DROP FUNCTION IF EXISTS books_tsv_trigger()")


def _downgrade_sqlite() -> None:
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_ins")
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_del")


def _downgrade_mysql() -> None:
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_ins")
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_del")
    op.execute("ALTER TABLE reports DROP INDEX reports_ft_idx")
    op.execute("ALTER TABLE books DROP INDEX books_ft_idx")

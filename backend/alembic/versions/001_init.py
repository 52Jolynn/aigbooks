"""initial schema: books / reports / evidences / votes + triggers + GIN indexes

Revision ID: 001
Revises:
Create Date: 2026-07-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger(), primary_key=True),
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
        sa.Column("tsv_meta", postgresql.TSVECTOR(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)

    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "book_id",
            sa.BigInteger(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tsv_desc", postgresql.TSVECTOR(), nullable=True),
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
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_reports_book_id", "reports", ["book_id"], unique=False)

    op.create_table(
        "evidences",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "report_id",
            sa.BigInteger(),
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
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_evidences_report_id", "evidences", ["report_id"], unique=False)

    op.create_table(
        "votes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "report_id",
            sa.BigInteger(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("vote_type", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("report_id", "ip", "fingerprint", name="uq_vote"),
    )

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
    op.create_index(
        "reports_rate_limit_idx",
        "reports",
        ["ip", "fingerprint", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("reports_rate_limit_idx", table_name="reports")
    op.drop_index("reports_tsv_desc_idx", table_name="reports")
    op.drop_index("books_tsv_meta_idx", table_name="books")

    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count ON reports")
    op.execute("DROP TRIGGER IF EXISTS reports_tsv_desc_trigger ON reports")
    op.execute("DROP TRIGGER IF EXISTS books_tsv_meta_trigger ON books")
    op.execute("DROP FUNCTION IF EXISTS update_book_report_count()")
    op.execute("DROP FUNCTION IF EXISTS reports_tsv_trigger()")
    op.execute("DROP FUNCTION IF EXISTS books_tsv_trigger()")

    op.drop_table("votes")
    op.drop_index("ix_evidences_report_id", table_name="evidences")
    op.drop_table("evidences")
    op.drop_index("ix_reports_book_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_books_isbn", table_name="books")
    op.drop_table("books")

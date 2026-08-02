"""002: books → identifiers (通用编号聚合根)

Revision ID: 002
Revises: 001
Create Date: 2026-08-02

迁移要点：
- 表 ``books`` rename 为 ``identifiers``
- 新增列 ``type VARCHAR(16) NOT NULL DEFAULT 'isbn'``
- 列 ``isbn`` rename 为 ``identifier``
- 唯一约束 ``uq_books_isbn`` 替换为 ``uq_identifiers_type_identifier``
- 索引 ``ix_books_isbn`` 替换为 ``ix_identifiers_type_identifier``
- ``reports.book_id`` rename 为 ``reports.identifier_id``
- 三方言分支：重建触发器/FTS5/FULLTEXT（因为表名变化，引用失效）

方言策略：
- PostgreSQL：直接 ``ALTER TABLE ... RENAME COLUMN`` + ``ADD COLUMN``
- MySQL：``ALTER TABLE ... CHANGE`` + ``ADD COLUMN``
- SQLite：12 步重建法（CREATE NEW → COPY → DROP OLD → RENAME）
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op
from app.db.constants import (
    DIALECT_MYSQL,
    DIALECT_POSTGRESQL,
    DIALECT_SQLITE,
)

revision: str = "002"
down_revision: str | str | None = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == DIALECT_POSTGRESQL:
        _upgrade_postgres()
    elif dialect == DIALECT_SQLITE:
        _upgrade_sqlite()
    elif dialect == DIALECT_MYSQL:
        _upgrade_mysql()
    else:
        raise RuntimeError(f"unsupported dialect: {dialect}")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == DIALECT_POSTGRESQL:
        _downgrade_postgres()
    elif dialect == DIALECT_SQLITE:
        _downgrade_sqlite()
    elif dialect == DIALECT_MYSQL:
        _downgrade_mysql()
    else:
        raise RuntimeError(f"unsupported dialect: {dialect}")


def _upgrade_postgres() -> None:
    """PG：直接 RENAME COLUMN + ADD COLUMN；触发器内表名引用更新。"""
    op.execute("ALTER TABLE books RENAME TO identifiers")
    op.execute("ALTER TABLE identifiers RENAME COLUMN isbn TO identifier")
    op.add_column(
        "identifiers",
        sa.Column("type", sa.String(16), nullable=False, server_default=sa.text("'isbn'")),
    )
    op.drop_constraint("uq_books_isbn", "identifiers", type_="unique")
    op.create_unique_constraint(
        "uq_identifiers_type_identifier", "identifiers", ["type", "identifier"]
    )
    op.drop_index("ix_books_isbn", table_name="identifiers")
    op.create_index(
        "ix_identifiers_type_identifier", "identifiers", ["type", "identifier"], unique=True
    )

    op.execute("ALTER TABLE reports RENAME COLUMN book_id TO identifier_id")
    op.execute("ALTER INDEX ix_reports_book_id RENAME TO ix_reports_identifier_id")

    _drop_postgres_triggers()
    _create_postgres_triggers()


def _drop_postgres_triggers() -> None:
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count ON reports")
    op.execute("DROP TRIGGER IF EXISTS reports_tsv_desc_trigger ON reports")
    op.execute("DROP TRIGGER IF EXISTS books_tsv_meta_trigger ON identifiers")
    op.execute("DROP FUNCTION IF EXISTS update_book_report_count()")
    op.execute("DROP FUNCTION IF EXISTS reports_tsv_trigger()")
    op.execute("DROP FUNCTION IF EXISTS books_tsv_trigger()")

    op.drop_index("reports_tsv_desc_idx", table_name="reports")
    op.drop_index("books_tsv_meta_idx", table_name="identifiers")


def _create_postgres_triggers() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION identifiers_tsv_trigger() RETURNS trigger AS $$
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
        CREATE TRIGGER identifiers_tsv_meta_trigger
            BEFORE INSERT OR UPDATE ON identifiers
            FOR EACH ROW EXECUTE FUNCTION identifiers_tsv_trigger();
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
        CREATE OR REPLACE FUNCTION update_identifier_report_count() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE identifiers SET report_count = report_count + 1 WHERE id = NEW.identifier_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE identifiers SET report_count = report_count - 1 WHERE id = OLD.identifier_id;
                RETURN OLD;
            END IF;
            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_identifier_report_count
            AFTER INSERT OR DELETE ON reports
            FOR EACH ROW EXECUTE FUNCTION update_identifier_report_count();
        """
    )

    op.create_index(
        "identifiers_tsv_meta_idx",
        "identifiers",
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
    """SQLite：12 步重建法（不支持直接 RENAME COLUMN 与 ADD CONSTRAINT）。"""
    _drop_sqlite_triggers()

    # 1. 重建 identifiers 表（含 type 列与新约束）
    op.execute(
        """
        CREATE TABLE identifiers_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            type          VARCHAR(16) NOT NULL DEFAULT 'isbn',
            identifier    TEXT NOT NULL,
            title         TEXT NOT NULL,
            author        TEXT NOT NULL,
            cover_path    TEXT,
            report_count  INTEGER NOT NULL DEFAULT 0,
            tsv_meta      TEXT,
            search_text   TEXT NOT NULL DEFAULT '',
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(type, identifier)
        )
        """
    )
    op.execute(
        """
        INSERT INTO identifiers_new
            (id, type, identifier, title, author, cover_path, report_count,
             tsv_meta, search_text, created_at, updated_at)
        SELECT id, 'isbn', isbn, title, author, cover_path, report_count,
               tsv_meta, search_text, created_at, updated_at
        FROM books
        """
    )
    op.drop_table("books")
    op.rename_table("identifiers_new", "identifiers")
    op.create_index(
        "ix_identifiers_type_identifier",
        "identifiers",
        ["type", "identifier"],
        unique=True,
    )

    # 2. 重建 reports 表（rename book_id → identifier_id，FK 重建）
    op.execute(
        """
        CREATE TABLE reports_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier_id INTEGER NOT NULL REFERENCES identifiers(id) ON DELETE CASCADE,
            description   TEXT NOT NULL,
            tsv_desc      TEXT,
            search_text   TEXT NOT NULL DEFAULT '',
            upvote        INTEGER NOT NULL DEFAULT 0,
            downvote      INTEGER NOT NULL DEFAULT 0,
            ip            VARCHAR(45) NOT NULL,
            fingerprint   TEXT NOT NULL,
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        INSERT INTO reports_new
            (id, identifier_id, description, tsv_desc, search_text, upvote, downvote,
             ip, fingerprint, created_at)
        SELECT id, book_id, description, tsv_desc, search_text, upvote, downvote,
               ip, fingerprint, created_at
        FROM reports
        """
    )
    op.drop_table("reports")
    op.rename_table("reports_new", "reports")
    op.create_index("ix_reports_identifier_id", "reports", ["identifier_id"], unique=False)
    op.create_index(
        "reports_rate_limit_idx",
        "reports",
        ["ip", "fingerprint", "created_at"],
        unique=False,
    )

    _create_sqlite_triggers()


def _drop_sqlite_triggers() -> None:
    """兼容新旧两种触发器名称（升级与降级共用）。"""
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_ins")
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_del")
    op.execute("DROP TRIGGER IF EXISTS maintain_identifier_report_count_ins")
    op.execute("DROP TRIGGER IF EXISTS maintain_identifier_report_count_del")
    op.execute("DROP TRIGGER IF EXISTS books_fts_ai")
    op.execute("DROP TRIGGER IF EXISTS books_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS books_fts_au")
    op.execute("DROP TRIGGER IF EXISTS identifiers_fts_ai")
    op.execute("DROP TRIGGER IF EXISTS identifiers_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS identifiers_fts_au")
    op.execute("DROP TRIGGER IF EXISTS reports_fts_ai")
    op.execute("DROP TRIGGER IF EXISTS reports_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS reports_fts_au")
    op.execute("DROP TABLE IF EXISTS books_fts")
    op.execute("DROP TABLE IF EXISTS identifiers_fts")
    op.execute("DROP TABLE IF EXISTS reports_fts")


def _create_sqlite_triggers() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE identifiers_fts USING fts5(
            search_text,
            content='identifiers', content_rowid='id',
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
        CREATE TRIGGER identifiers_fts_ai AFTER INSERT ON identifiers BEGIN
            INSERT INTO identifiers_fts(rowid, search_text) VALUES (new.id, new.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER identifiers_fts_ad AFTER DELETE ON identifiers BEGIN
            INSERT INTO identifiers_fts(identifiers_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER identifiers_fts_au AFTER UPDATE ON identifiers BEGIN
            INSERT INTO identifiers_fts(identifiers_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
            INSERT INTO identifiers_fts(rowid, search_text) VALUES (new.id, new.search_text);
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
        CREATE TRIGGER maintain_identifier_report_count_ins
            AFTER INSERT ON reports
            BEGIN
                UPDATE identifiers SET report_count = report_count + 1 WHERE id = NEW.identifier_id;
            END
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_identifier_report_count_del
            AFTER DELETE ON reports
            BEGIN
                UPDATE identifiers SET report_count = report_count - 1 WHERE id = OLD.identifier_id;
            END
        """
    )


def _upgrade_mysql() -> None:
    """MySQL：CHANGE COLUMN + ADD COLUMN + DROP/CREATE 触发器。"""
    _drop_mysql_triggers()

    op.execute("ALTER TABLE books RENAME TO identifiers")
    op.execute("ALTER TABLE identifiers CHANGE isbn identifier TEXT NOT NULL")
    op.add_column(
        "identifiers",
        sa.Column("type", sa.String(16), nullable=False, server_default=sa.text("'isbn'")),
    )
    op.drop_constraint("uq_books_isbn", "identifiers", type_="unique")
    op.create_unique_constraint(
        "uq_identifiers_type_identifier", "identifiers", ["type", "identifier"]
    )
    op.drop_index("ix_books_isbn", table_name="identifiers")
    op.create_index(
        "ix_identifiers_type_identifier", "identifiers", ["type", "identifier"], unique=True
    )

    op.execute("ALTER TABLE reports DROP FOREIGN KEY reports_ibfk_1")
    op.execute("ALTER TABLE reports CHANGE book_id identifier_id BIGINT NOT NULL")
    op.execute(
        "ALTER TABLE reports ADD CONSTRAINT reports_identifier_id_fkey "
        "FOREIGN KEY (identifier_id) REFERENCES identifiers(id) ON DELETE CASCADE"
    )
    op.drop_index("ix_reports_book_id", table_name="reports")
    op.create_index("ix_reports_identifier_id", "reports", ["identifier_id"], unique=False)

    _create_mysql_triggers()


def _drop_mysql_triggers() -> None:
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_ins")
    op.execute("DROP TRIGGER IF EXISTS maintain_book_report_count_del")
    op.execute("ALTER TABLE reports DROP INDEX reports_ft_idx")
    op.execute("ALTER TABLE identifiers DROP INDEX books_ft_idx")


def _create_mysql_triggers() -> None:
    op.execute(
        "ALTER TABLE identifiers ADD FULLTEXT INDEX identifiers_ft_idx (title, author) WITH PARSER ngram"
    )
    op.execute(
        "ALTER TABLE reports ADD FULLTEXT INDEX reports_ft_idx (description) WITH PARSER ngram"
    )
    op.execute(
        """
        CREATE TRIGGER maintain_identifier_report_count_ins
        AFTER INSERT ON reports FOR EACH ROW
        UPDATE identifiers SET report_count = report_count + 1 WHERE id = NEW.identifier_id
        """
    )
    op.execute(
        """
        CREATE TRIGGER maintain_identifier_report_count_del
        AFTER DELETE ON reports FOR EACH ROW
        UPDATE identifiers SET report_count = report_count - 1 WHERE id = OLD.identifier_id
        """
    )


def _downgrade_postgres() -> None:
    _drop_postgres_triggers()
    op.execute("ALTER TABLE reports RENAME COLUMN identifier_id TO book_id")
    op.execute("ALTER INDEX ix_reports_identifier_id RENAME TO ix_reports_book_id")
    op.execute("ALTER TABLE identifiers RENAME COLUMN identifier TO isbn")
    op.drop_column("identifiers", "type")
    op.drop_index("ix_identifiers_type_identifier", table_name="identifiers")
    op.create_index("ix_books_isbn", "identifiers", ["isbn"], unique=True)
    op.drop_constraint("uq_identifiers_type_identifier", "identifiers", type_="unique")
    op.create_unique_constraint("uq_books_isbn", "identifiers", ["isbn"])
    op.rename_table("identifiers", "books")
    _create_postgres_triggers_original()


def _create_postgres_triggers_original() -> None:
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


def _downgrade_sqlite() -> None:
    _drop_sqlite_triggers()

    # 1. 重建 books 表（用 identifiers 数据回填 isbn 列）
    op.execute(
        """
        CREATE TABLE books_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn          TEXT NOT NULL,
            title         TEXT NOT NULL,
            author        TEXT NOT NULL,
            cover_path    TEXT,
            report_count  INTEGER NOT NULL DEFAULT 0,
            tsv_meta      TEXT,
            search_text   TEXT NOT NULL DEFAULT '',
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(isbn)
        )
        """
    )
    op.execute(
        """
        INSERT INTO books_new
            (id, isbn, title, author, cover_path, report_count,
             tsv_meta, search_text, created_at, updated_at)
        SELECT id, identifier, title, author, cover_path, report_count,
               tsv_meta, search_text, created_at, updated_at
        FROM identifiers
        """
    )
    op.drop_table("identifiers")
    op.rename_table("books_new", "books")
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)

    # 2. 重建 reports 表（rename identifier_id → book_id）
    op.execute(
        """
        CREATE TABLE reports_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id       INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            description   TEXT NOT NULL,
            tsv_desc      TEXT,
            search_text   TEXT NOT NULL DEFAULT '',
            upvote        INTEGER NOT NULL DEFAULT 0,
            downvote      INTEGER NOT NULL DEFAULT 0,
            ip            VARCHAR(45) NOT NULL,
            fingerprint   TEXT NOT NULL,
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        INSERT INTO reports_new
            (id, book_id, description, tsv_desc, search_text, upvote, downvote,
             ip, fingerprint, created_at)
        SELECT id, identifier_id, description, tsv_desc, search_text, upvote, downvote,
               ip, fingerprint, created_at
        FROM reports
        """
    )
    op.drop_table("reports")
    op.rename_table("reports_new", "reports")
    op.create_index("ix_reports_book_id", "reports", ["book_id"], unique=False)
    op.create_index(
        "reports_rate_limit_idx",
        "reports",
        ["ip", "fingerprint", "created_at"],
        unique=False,
    )

    # 注意：此处不调用 _create_sqlite_triggers_original()，
    # 保持 001.downgrade() 调用时 DB 中无 FTS5 影子表与触发器，
    # 避免 001.downgrade() 后续 CREATE TABLE books 时触发残留冲突。


def _create_sqlite_triggers_original() -> None:
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


def _downgrade_mysql() -> None:
    _drop_mysql_triggers()
    op.execute("ALTER TABLE reports DROP FOREIGN KEY reports_identifier_id_fkey")
    op.execute("ALTER TABLE reports CHANGE identifier_id book_id BIGINT NOT NULL")
    op.execute(
        "ALTER TABLE reports ADD CONSTRAINT reports_book_id_fkey "
        "FOREIGN KEY (book_id) REFERENCES identifiers(id) ON DELETE CASCADE"
    )
    op.drop_index("ix_reports_identifier_id", table_name="reports")
    op.create_index("ix_reports_book_id", "reports", ["book_id"], unique=False)
    op.execute("ALTER TABLE identifiers DROP INDEX ix_identifiers_type_identifier")
    op.execute("ALTER TABLE identifiers CHANGE identifier isbn TEXT NOT NULL")
    op.drop_column("identifiers", "type")
    op.drop_constraint("uq_identifiers_type_identifier", "identifiers", type_="unique")
    op.create_unique_constraint("uq_books_isbn", "identifiers", ["isbn"])
    op.create_index("ix_books_isbn", "identifiers", ["isbn"], unique=True)
    op.rename_table("identifiers", "books")
    _create_mysql_triggers_original()


def _create_mysql_triggers_original() -> None:
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

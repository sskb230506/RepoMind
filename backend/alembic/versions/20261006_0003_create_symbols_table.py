"""create symbols table

Revision ID: 0003_create_symbols_table
Revises: 0002_create_repository_files_table
Create Date: 2026-10-06 10:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_create_symbols_table"
down_revision: str | Sequence[str] | None = "0002_create_repository_files_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "symbols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("symbol_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("qualified_name", sa.String(length=1024), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("parent_symbol_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_symbols_repository_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["repository_files.id"],
            name="fk_symbols_file_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_symbol_id"],
            ["symbols.id"],
            name="fk_symbols_parent_symbol_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_symbols_id"), "symbols", ["id"], unique=False)
    op.create_index(
        op.f("ix_symbols_repository_id"), "symbols", ["repository_id"], unique=False
    )
    op.create_index(op.f("ix_symbols_file_id"), "symbols", ["file_id"], unique=False)
    op.create_index(
        op.f("ix_symbols_symbol_type"), "symbols", ["symbol_type"], unique=False
    )
    op.create_index(op.f("ix_symbols_name"), "symbols", ["name"], unique=False)
    op.create_index(
        op.f("ix_symbols_qualified_name"), "symbols", ["qualified_name"], unique=False
    )
    op.create_index(
        op.f("ix_symbols_parent_symbol_id"),
        "symbols",
        ["parent_symbol_id"],
        unique=False,
    )
    op.create_index(
        "ix_symbols_repo_symbol_type",
        "symbols",
        ["repository_id", "symbol_type"],
        unique=False,
    )
    op.create_index(
        "ix_symbols_file_symbol_type",
        "symbols",
        ["file_id", "symbol_type"],
        unique=False,
    )
    op.create_index(
        "ix_symbols_repo_name",
        "symbols",
        ["repository_id", "name"],
        unique=False,
    )
    op.create_index(
        "ix_symbols_repo_qualified_name",
        "symbols",
        ["repository_id", "qualified_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_symbols_repo_qualified_name", table_name="symbols")
    op.drop_index("ix_symbols_repo_name", table_name="symbols")
    op.drop_index("ix_symbols_file_symbol_type", table_name="symbols")
    op.drop_index("ix_symbols_repo_symbol_type", table_name="symbols")
    op.drop_index(op.f("ix_symbols_parent_symbol_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_qualified_name"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_name"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_symbol_type"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_file_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_repository_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_id"), table_name="symbols")
    op.drop_table("symbols")

"""create repository_files table

Revision ID: 0002_create_repository_files_table
Revises: 0001_create_repositories_table
Create Date: 2026-10-06 08:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_create_repository_files_table"
down_revision: str | Sequence[str] | None = "0001_create_repositories_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repository_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_binary", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_generated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_repository_files_repository_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id", "path", name="uq_repository_files_repo_path"
        ),
    )
    op.create_index(
        op.f("ix_repository_files_id"), "repository_files", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_repository_files_repository_id"),
        "repository_files",
        ["repository_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repository_files_path"), "repository_files", ["path"], unique=False
    )
    op.create_index(
        op.f("ix_repository_files_filename"),
        "repository_files",
        ["filename"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repository_files_extension"),
        "repository_files",
        ["extension"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repository_files_language"),
        "repository_files",
        ["language"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_repository_files_language"), table_name="repository_files")
    op.drop_index(op.f("ix_repository_files_extension"), table_name="repository_files")
    op.drop_index(op.f("ix_repository_files_filename"), table_name="repository_files")
    op.drop_index(op.f("ix_repository_files_path"), table_name="repository_files")
    op.drop_index(
        op.f("ix_repository_files_repository_id"), table_name="repository_files"
    )
    op.drop_index(op.f("ix_repository_files_id"), table_name="repository_files")
    op.drop_table("repository_files")

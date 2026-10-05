"""create repositories table

Revision ID: 0001_create_repositories_table
Revises:
Create Date: 2026-10-05 16:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_create_repositories_table"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("github_url", sa.String(length=512), nullable=False),
        sa.Column(
            "default_branch",
            sa.String(length=64),
            server_default="main",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "indexing",
                "ready",
                "failed",
                name="repository_status",
                native_enum=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_url", name="uq_repositories_github_url"),
    )
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"], unique=False)
    op.create_index(
        op.f("ix_repositories_name"), "repositories", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_repositories_github_url"), "repositories", ["github_url"], unique=True
    )
    op.create_index(
        op.f("ix_repositories_status"), "repositories", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_repositories_status"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_github_url"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_name"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_table("repositories")

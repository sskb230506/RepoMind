from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.db.base import Base
except ModuleNotFoundError:
    from app.db.base import Base

if TYPE_CHECKING:
    from .repository_file import RepositoryFile


class RepositoryStatus(StrEnum):
    """Possible lifecycle states for an indexed repository."""

    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    """Repository entity representing a connected GitHub repository."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    github_url: Mapped[str] = mapped_column(
        String(512), nullable=False, unique=True, index=True
    )
    default_branch: Mapped[str] = mapped_column(
        String(64), nullable=False, default="main"
    )
    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus, name="repository_status", native_enum=False),
        nullable=False,
        default=RepositoryStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    files: Mapped[list["RepositoryFile"]] = relationship(
        "RepositoryFile",
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Repository(id={self.id}, name='{self.name}', "
            f"status='{self.status.value}')>"
        )

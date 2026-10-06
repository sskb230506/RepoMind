from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.db.base import Base
except ModuleNotFoundError:
    from app.db.base import Base

if TYPE_CHECKING:
    from .repository import Repository
    from .symbol import Symbol


class RepositoryFile(Base):
    """File record representing scanned source/asset files in an ingested repository."""

    __tablename__ = "repository_files"

    __table_args__ = (
        UniqueConstraint("repository_id", "path", name="uq_repository_files_repo_path"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    extension: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_binary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="files"
    )
    symbols: Mapped[list["Symbol"]] = relationship(
        "Symbol", back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<RepositoryFile(id={self.id}, repo_id={self.repository_id}, "
            f"path='{self.path}', lang='{self.language}')>"
        )

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.db.base import Base
except ModuleNotFoundError:
    from app.db.base import Base

if TYPE_CHECKING:
    from .repository import Repository
    from .repository_file import RepositoryFile


class Symbol(Base):
    """
    Source code symbol extracted by the AST parser (functions, methods, classes,
    imports, exports, function calls, inheritance relationships, and definitions).
    """

    __tablename__ = "symbols"

    __table_args__ = (
        Index("ix_symbols_repo_symbol_type", "repository_id", "symbol_type"),
        Index("ix_symbols_file_symbol_type", "file_id", "symbol_type"),
        Index("ix_symbols_repo_name", "repository_id", "name"),
        Index("ix_symbols_repo_qualified_name", "repository_id", "qualified_name"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qualified_name: Mapped[str] = mapped_column(
        String(1024), nullable=False, index=True
    )
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_symbol_id: Mapped[int | None] = mapped_column(
        ForeignKey("symbols.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="symbols"
    )
    file: Mapped["RepositoryFile"] = relationship(
        "RepositoryFile", back_populates="symbols"
    )
    parent: Mapped["Symbol | None"] = relationship(
        "Symbol", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Symbol"]] = relationship(
        "Symbol", back_populates="parent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Symbol(id={self.id}, type='{self.symbol_type}', "
            f"name='{self.name}', qname='{self.qualified_name}')>"
        )

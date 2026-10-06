from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RepositoryFileResponse(BaseModel):
    """File metadata record in a repository inventory."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    path: str
    filename: str
    extension: str
    language: str | None
    size_bytes: int
    is_binary: bool
    is_generated: bool
    created_at: datetime


class PaginatedRepositoryFilesResponse(BaseModel):
    """Paginated list of scanned repository files."""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[RepositoryFileResponse]

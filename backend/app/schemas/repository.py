from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

try:
    from backend.app.models.repository import RepositoryStatus
except ModuleNotFoundError:
    from app.models.repository import RepositoryStatus


class RepositoryCreate(BaseModel):
    """Payload for registering and ingesting a GitHub repository."""

    github_url: str = Field(
        ...,
        description="Public GitHub repository URL (e.g. https://github.com/owner/repository)",
        examples=["https://github.com/octocat/Hello-World"],
    )


class RepositoryResponse(BaseModel):
    """Public representation of a repository and its ingestion state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    github_url: str
    default_branch: str
    status: RepositoryStatus
    created_at: datetime
    updated_at: datetime

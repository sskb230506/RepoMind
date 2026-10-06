from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.db.session import get_db
    from backend.app.models.repository import Repository
    from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse
    from backend.app.services.ingestion import (
        GitCloneError,
        IngestionError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        ingest_repository,
    )
except ModuleNotFoundError:
    from app.db.session import get_db
    from app.models.repository import Repository
    from app.schemas.repository import RepositoryCreate, RepositoryResponse
    from app.services.ingestion import (
        GitCloneError,
        IngestionError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        ingest_repository,
    )

router = APIRouter()


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a GitHub repository",
    description=(
        "Validates the GitHub URL, creates a database record, safely clones "
        "the repository into an isolated workspace, detects the default branch, "
        "and returns the repository ID and ingestion status."
    ),
)
def create_repository(
    payload: RepositoryCreate,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    """
    Ingest a GitHub repository into RepoMind.
    """
    try:
        repo = ingest_repository(db, payload.github_url)
        return repo
    except InvalidGitHubURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RepositoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except RepoLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except GitCloneError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to clone repository: {exc}",
        ) from exc
    except IngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during repository ingestion.",
        ) from exc


@router.get(
    "",
    response_model=list[RepositoryResponse],
    summary="List all repositories",
)
def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[RepositoryResponse]:
    """
    Retrieve all registered repositories.
    """
    repos = db.query(Repository).offset(skip).limit(limit).all()
    return repos


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
    summary="Get repository by ID",
)
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    """
    Retrieve repository metadata and current ingestion status.
    """
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )
    return repo

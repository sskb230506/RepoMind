import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from backend.app.db.session import get_db
    from backend.app.models.repository import Repository
    from backend.app.models.repository_file import RepositoryFile
    from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse
    from backend.app.schemas.repository_file import PaginatedRepositoryFilesResponse
    from backend.app.services.ingestion import (
        GitCloneError,
        IngestionError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        get_repo_storage_path,
        ingest_repository,
    )
    from backend.app.services.scanner import scan_repository_files
except ModuleNotFoundError:
    from app.db.session import get_db
    from app.models.repository import Repository
    from app.models.repository_file import RepositoryFile
    from app.schemas.repository import RepositoryCreate, RepositoryResponse
    from app.schemas.repository_file import PaginatedRepositoryFilesResponse
    from app.services.ingestion import (
        GitCloneError,
        IngestionError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        get_repo_storage_path,
        ingest_repository,
    )
    from app.services.scanner import scan_repository_files

router = APIRouter()


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a GitHub repository",
    description=(
        "Validates the GitHub URL, creates a database record, safely clones "
        "the repository into an isolated workspace, detects the default branch, "
        "scans files into inventory, and returns repository ID and status."
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


@router.get(
    "/{repository_id}/files",
    response_model=PaginatedRepositoryFilesResponse,
    summary="Get paginated repository files",
    description=(
        "Returns paginated file inventory for an ingested repository "
        "with optional filtering."
    ),
)
def get_repository_files(
    repository_id: int,
    page: int = Query(1, ge=1, description="Page number starting from 1"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    language: str | None = Query(None, description="Filter by programming language"),
    is_binary: bool | None = Query(None, description="Filter binary files"),
    is_generated: bool | None = Query(
        None, description="Filter generated/minified files"
    ),
    path_prefix: str | None = Query(None, description="Filter by file path prefix"),
    db: Session = Depends(get_db),
) -> PaginatedRepositoryFilesResponse:
    """
    Retrieve paginated file inventory for the given repository.
    """
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    query = db.query(RepositoryFile).filter(
        RepositoryFile.repository_id == repository_id
    )

    if language:
        query = query.filter(RepositoryFile.language.ilike(language))
    if is_binary is not None:
        query = query.filter(RepositoryFile.is_binary == is_binary)
    if is_generated is not None:
        query = query.filter(RepositoryFile.is_generated == is_generated)
    if path_prefix:
        clean_prefix = path_prefix.strip("/").rstrip("/")
        query = query.filter(RepositoryFile.path.startswith(clean_prefix))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = (
        query.order_by(RepositoryFile.path.asc()).offset(offset).limit(page_size).all()
    )

    return PaginatedRepositoryFilesResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.post(
    "/{repository_id}/scan",
    response_model=PaginatedRepositoryFilesResponse,
    summary="Rescan repository files",
    description=(
        "Rescans the repository workspace on disk and refreshes the file inventory."
    ),
)
def rescan_repository_files(
    repository_id: int,
    db: Session = Depends(get_db),
) -> PaginatedRepositoryFilesResponse:
    """
    Manually trigger a rescan of repository files on disk.
    """
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found.",
        )

    repo_dir = get_repo_storage_path(repo.id)
    if not repo_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository storage workspace does not exist on disk.",
        )

    items = scan_repository_files(db, repo.id, repo_dir)
    return PaginatedRepositoryFilesResponse(
        total=len(items),
        page=1,
        page_size=max(len(items), 1),
        total_pages=1,
        items=items,
    )

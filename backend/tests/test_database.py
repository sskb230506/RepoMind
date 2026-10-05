import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from backend.app.db.session import check_db_connection
    from backend.app.models.repository import Repository, RepositoryStatus
except ModuleNotFoundError:
    from app.db.session import check_db_connection
    from app.models.repository import Repository, RepositoryStatus


def test_database_connection(db_session: Session):
    """Test that a connection to the database can be acquired and executed."""
    # Test raw text query execution on the session
    result = db_session.execute(text("SELECT 1 AS alive")).scalar()
    assert result == 1


def test_check_db_connection_utility(db_session: Session):
    """Test the check_db_connection utility against an active engine."""
    # Obtain the engine bound to the active session
    active_engine = db_session.get_bind()
    assert check_db_connection(target=active_engine) is True


def test_repository_creation(db_session: Session):
    """Test creating a new Repository record and verifying persistence."""
    repo = Repository(
        name="RepoMind",
        github_url="https://github.com/sskb230506/RepoMind",
        default_branch="main",
        status=RepositoryStatus.PENDING,
    )

    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    assert repo.id is not None
    assert isinstance(repo.id, int)
    assert repo.name == "RepoMind"
    assert repo.github_url == "https://github.com/sskb230506/RepoMind"
    assert repo.default_branch == "main"
    assert repo.status == RepositoryStatus.PENDING
    assert repo.created_at is not None
    assert repo.updated_at is not None


def test_repository_retrieval(db_session: Session):
    """Test retrieving repository records by ID, URL, and status."""
    repo = Repository(
        name="FastAPI",
        github_url="https://github.com/tiangolo/fastapi",
        default_branch="master",
        status=RepositoryStatus.READY,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    # 1. Retrieval by primary key ID
    retrieved_by_id = db_session.get(Repository, repo.id)
    assert retrieved_by_id is not None
    assert retrieved_by_id.name == "FastAPI"
    assert retrieved_by_id.github_url == "https://github.com/tiangolo/fastapi"
    assert retrieved_by_id.status == RepositoryStatus.READY

    # 2. Retrieval by unique github_url
    retrieved_by_url = (
        db_session.query(Repository)
        .filter(Repository.github_url == "https://github.com/tiangolo/fastapi")
        .first()
    )
    assert retrieved_by_url is not None
    assert retrieved_by_url.id == repo.id

    # 3. Retrieval of non-existent ID returns None
    missing = db_session.get(Repository, 999999)
    assert missing is None


def test_repository_status_transitions(db_session: Session):
    """Test updating repository status across supported states."""
    repo = Repository(
        name="LifecycleTest",
        github_url="https://github.com/example/lifecycle",
        default_branch="main",
        status=RepositoryStatus.PENDING,
    )
    db_session.add(repo)
    db_session.commit()
    assert repo.status == RepositoryStatus.PENDING

    # Transition to indexing
    repo.status = RepositoryStatus.INDEXING
    db_session.commit()
    db_session.refresh(repo)
    assert repo.status == RepositoryStatus.INDEXING

    # Transition to ready
    repo.status = RepositoryStatus.READY
    db_session.commit()
    db_session.refresh(repo)
    assert repo.status == RepositoryStatus.READY

    # Transition to failed
    repo.status = RepositoryStatus.FAILED
    db_session.commit()
    db_session.refresh(repo)
    assert repo.status == RepositoryStatus.FAILED


def test_repository_unique_github_url(db_session: Session):
    """Test that duplicate github_url raises an IntegrityError."""
    repo1 = Repository(
        name="Original",
        github_url="https://github.com/duplicate/test",
        default_branch="main",
        status=RepositoryStatus.PENDING,
    )
    db_session.add(repo1)
    db_session.commit()

    repo2 = Repository(
        name="Duplicate",
        github_url="https://github.com/duplicate/test",
        default_branch="main",
        status=RepositoryStatus.PENDING,
    )
    db_session.add(repo2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

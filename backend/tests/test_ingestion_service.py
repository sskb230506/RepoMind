from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

try:
    from backend.app.core.config import settings
    from backend.app.models.repository import Repository, RepositoryStatus
    from backend.app.services.ingestion import (
        GitCloneError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        detect_default_branch,
        get_repo_storage_path,
        ingest_repository,
        validate_github_url,
        validate_repo_limits,
    )
except ModuleNotFoundError:
    from app.core.config import settings
    from app.models.repository import Repository, RepositoryStatus
    from app.services.ingestion import (
        GitCloneError,
        InvalidGitHubURLError,
        RepoLimitExceededError,
        RepositoryAlreadyExistsError,
        get_repo_storage_path,
        ingest_repository,
        validate_github_url,
        validate_repo_limits,
    )


class TestGitHubUrlValidation:
    """Test URL parsing, schema constraints, and SSRF prevention."""

    def test_valid_standard_urls(self):
        url, owner, repo = validate_github_url("https://github.com/octocat/Hello-World")
        assert url == "https://github.com/octocat/Hello-World"
        assert owner == "octocat"
        assert repo == "Hello-World"

    def test_valid_dot_git_suffix(self):
        url, owner, repo = validate_github_url("https://github.com/torvalds/linux.git")
        assert url == "https://github.com/torvalds/linux"
        assert owner == "torvalds"
        assert repo == "linux"

    def test_valid_http_normalized_to_https(self):
        url, owner, repo = validate_github_url("http://github.com/pallets/flask/")
        assert url == "https://github.com/pallets/flask"
        assert owner == "pallets"
        assert repo == "flask"

    def test_valid_subdomain_www(self):
        url, owner, repo = validate_github_url("https://www.github.com/psf/requests")
        assert url == "https://github.com/psf/requests"
        assert owner == "psf"
        assert repo == "requests"

    def test_invalid_empty_and_non_string(self):
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url("")
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url(None)  # type: ignore

    def test_invalid_foreign_hosts_prevent_ssrf(self):
        with pytest.raises(InvalidGitHubURLError, match="Only 'github.com' is allowed"):
            validate_github_url("https://gitlab.com/owner/repo")
        with pytest.raises(InvalidGitHubURLError, match="Only 'github.com' is allowed"):
            validate_github_url("http://localhost/owner/repo")
        with pytest.raises(InvalidGitHubURLError, match="Only 'github.com' is allowed"):
            validate_github_url("http://127.0.0.1/owner/repo")
        with pytest.raises(InvalidGitHubURLError, match="Only 'github.com' is allowed"):
            validate_github_url("http://169.254.169.254/latest/meta-data")

    def test_invalid_scheme(self):
        with pytest.raises(InvalidGitHubURLError, match="Unsupported scheme"):
            validate_github_url("ftp://github.com/owner/repo")
        with pytest.raises(InvalidGitHubURLError, match="Unsupported scheme"):
            validate_github_url("file:///etc/passwd")

    def test_path_traversal_attempts(self):
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url("https://github.com/../evil")
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url("https://github.com/owner/..")

    def test_malformed_path_structure(self):
        # Missing repo
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url("https://github.com/onlyowner")
        # Subpath
        with pytest.raises(InvalidGitHubURLError):
            validate_github_url("https://github.com/owner/repo/tree/main")


class TestStorageAndSecurity:
    """Test filesystem isolation and limits."""

    def test_storage_path_containment(self):
        storage_path = get_repo_storage_path(42)
        expected_root = Path(settings.REPO_STORAGE_PATH).resolve()
        assert storage_path.is_relative_to(expected_root)
        assert storage_path.name == "repo_42"

    def test_validate_repo_limits_success(self, tmp_path: Path):
        test_file = tmp_path / "hello.py"
        test_file.write_text("print('hello')")
        # Should pass without exception
        validate_repo_limits(tmp_path)

    def test_validate_repo_limits_file_count_exceeded(
        self, tmp_path: Path, monkeypatch
    ):
        monkeypatch.setattr(settings, "MAX_REPO_FILE_COUNT", 2)
        for i in range(3):
            (tmp_path / f"file_{i}.txt").write_text("content")

        with pytest.raises(RepoLimitExceededError, match="file limit"):
            validate_repo_limits(tmp_path)

    def test_validate_repo_limits_size_exceeded(self, tmp_path: Path, monkeypatch):
        # Set max to 1 MB and write 2 MB
        monkeypatch.setattr(settings, "MAX_REPO_SIZE_MB", 1)
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"0" * (2 * 1024 * 1024))

        with pytest.raises(RepoLimitExceededError, match="size limit"):
            validate_repo_limits(tmp_path)

    def test_detect_default_branch_fallback(self, tmp_path: Path):
        branch = detect_default_branch(tmp_path)
        assert branch == "main"


class TestIngestionWorkflow:
    """Test full repository ingestion workflow."""

    @patch("backend.app.services.ingestion.clone_repository")
    @patch(
        "backend.app.services.ingestion.detect_default_branch", return_value="develop"
    )
    def test_ingest_repository_success(
        self, mock_branch, mock_clone, db_session: Session, tmp_path: Path, monkeypatch
    ):
        monkeypatch.setattr(settings, "REPO_STORAGE_PATH", str(tmp_path))

        repo = ingest_repository(db_session, "https://github.com/tiangolo/fastapi")

        assert repo.id is not None
        assert repo.name == "tiangolo/fastapi"
        assert repo.github_url == "https://github.com/tiangolo/fastapi"
        assert repo.default_branch == "develop"
        assert repo.status == RepositoryStatus.READY

        # Verify DB persistence
        retrieved = db_session.get(Repository, repo.id)
        assert retrieved is not None
        assert retrieved.status == RepositoryStatus.READY

    @patch("backend.app.services.ingestion.clone_repository")
    def test_ingest_repository_already_exists(
        self, mock_clone, db_session: Session, tmp_path: Path, monkeypatch
    ):
        monkeypatch.setattr(settings, "REPO_STORAGE_PATH", str(tmp_path))

        # First ingestion
        ingest_repository(db_session, "https://github.com/psf/black")

        # Second ingestion should raise
        with pytest.raises(RepositoryAlreadyExistsError, match="already been ingested"):
            ingest_repository(db_session, "https://github.com/psf/black")

    @patch(
        "backend.app.services.ingestion.clone_repository",
        side_effect=GitCloneError("Auth failed"),
    )
    def test_ingest_repository_clone_failure(
        self, mock_clone, db_session: Session, tmp_path: Path, monkeypatch
    ):
        monkeypatch.setattr(settings, "REPO_STORAGE_PATH", str(tmp_path))

        with pytest.raises(GitCloneError):
            ingest_repository(db_session, "https://github.com/private/repo")

        # Record should exist with FAILED status
        failed_repo = (
            db_session.query(Repository)
            .filter(Repository.github_url == "https://github.com/private/repo")
            .first()
        )
        assert failed_repo is not None
        assert failed_repo.status == RepositoryStatus.FAILED

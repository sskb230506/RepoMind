import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

try:
    from backend.app.core.config import settings
    from backend.app.models.repository import Repository, RepositoryStatus
    from backend.app.services.scanner import scan_repository_files
except ModuleNotFoundError:
    from app.core.config import settings
    from app.models.repository import Repository, RepositoryStatus
    from app.services.scanner import scan_repository_files

logger = logging.getLogger(__name__)

# GitHub naming constraints
OWNER_REGEX = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")
REPO_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{1,100}$")


class IngestionError(Exception):
    """Base exception for repository ingestion failures."""

    pass


class InvalidGitHubURLError(IngestionError):
    """Raised when the provided GitHub repository URL is invalid or malformed."""

    pass


class RepositoryAlreadyExistsError(IngestionError):
    """Raised when attempting to ingest a repository that already exists."""

    pass


class GitCloneError(IngestionError):
    """Raised when git clone fails."""

    pass


class RepoLimitExceededError(IngestionError):
    """Raised when repository exceeds disk size or file count limits."""

    pass


def validate_github_url(raw_url: str) -> tuple[str, str, str]:
    """
    Validate and sanitize a GitHub repository URL.

    Security checks:
    - Scheme must be https (http is accepted and normalized to https).
    - Host must strictly be github.com or www.github.com (prevents SSRF).
    - Port must be standard/empty.
    - Owner and repository names must match strict character sets (no path traversal).

    Returns:
        tuple[clean_url, owner, repo_name]
    """
    if not raw_url or not isinstance(raw_url, str):
        raise InvalidGitHubURLError("GitHub repository URL must be a non-empty string.")

    cleaned_input = raw_url.strip()
    try:
        parsed = urlparse(cleaned_input)
    except Exception as exc:
        raise InvalidGitHubURLError(f"Invalid URL syntax: {exc}") from exc

    # Validate scheme
    if parsed.scheme.lower() not in ("https", "http"):
        raise InvalidGitHubURLError(
            f"Unsupported scheme '{parsed.scheme}'. Only 'https' is permitted."
        )

    # Validate hostname (Defense against SSRF)
    hostname = (parsed.hostname or "").lower()
    if hostname not in ("github.com", "www.github.com"):
        raise InvalidGitHubURLError(
            f"Invalid repository host '{hostname}'. Only 'github.com' is allowed."
        )

    # Validate port
    if parsed.port and parsed.port not in (80, 443):
        raise InvalidGitHubURLError("Custom network ports are not permitted.")

    # Parse and validate path: /owner/repo[.git]
    path = parsed.path.strip("/").rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]

    parts = [p for p in path.split("/") if p]
    if len(parts) != 2:
        raise InvalidGitHubURLError(
            "GitHub URL must strictly follow the format: 'https://github.com/owner/repository'."
        )

    owner, repo_name = parts[0], parts[1]

    # Check for path traversal elements
    if owner in (".", "..") or repo_name in (".", ".."):
        raise InvalidGitHubURLError("Path traversal sequences are strictly forbidden.")

    if not OWNER_REGEX.match(owner):
        raise InvalidGitHubURLError(
            f"Invalid GitHub owner format: '{owner}'. "
            "Must be 1-39 alphanumeric characters."
        )

    if not REPO_NAME_REGEX.match(repo_name):
        raise InvalidGitHubURLError(f"Invalid repository name format: '{repo_name}'.")

    clean_url = f"https://github.com/{owner}/{repo_name}"
    return clean_url, owner, repo_name


def get_repo_storage_path(repo_id: int) -> Path:
    """
    Determine safe, isolated server storage path for the given repository ID.

    Security guarantee:
    - Path traversal is prevented by resolving and checking relative containment
      within the configured REPO_STORAGE_PATH.
    - Absolute filesystem paths are never returned to the user API.
    """
    storage_root = Path(settings.REPO_STORAGE_PATH).resolve()
    repo_dir = (storage_root / f"repo_{repo_id}").resolve()

    if not repo_dir.is_relative_to(storage_root):
        raise IngestionError("Security violation: resolved path escapes storage root.")

    return repo_dir


def clone_repository(
    clean_url: str,
    dest_dir: Path,
    timeout_seconds: int | None = None,
) -> None:
    """
    Safely clone a repository using shallow fetch and disabled hooks.

    Security guarantees:
    - Disables core.hooksPath to prevent arbitrary code execution on clone.
    - Uses shallow clone (--depth 1) to conserve network and disk resources.
    - Restricts git submodules code execution.
    - Executes via subprocess list without shell=True to prevent shell injection.
    """
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)

    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    timeout = timeout_seconds or settings.GIT_CLONE_TIMEOUT_SECONDS

    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--config",
        "core.hooksPath=/dev/null",  # Never run arbitrary repo hooks
        clean_url,
        str(dest_dir),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise GitCloneError(
            f"Git clone operation timed out after {timeout} seconds."
        ) from exc
    except Exception as exc:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise GitCloneError(f"Unexpected error running git clone: {exc}") from exc

    if result.returncode != 0:
        shutil.rmtree(dest_dir, ignore_errors=True)
        err_msg = (result.stderr or result.stdout or "Unknown git error").strip()
        logger.warning("Git clone failed with code %d: %s", result.returncode, err_msg)
        raise GitCloneError(f"Git clone failed: {err_msg}")


def validate_repo_limits(repo_dir: Path) -> None:
    """
    Enforce sensible repository size and file count limits.
    """
    max_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024
    max_files = settings.MAX_REPO_FILE_COUNT
    total_size = 0
    file_count = 0

    for root, _, files in os.walk(repo_dir):
        file_count += len(files)
        if file_count > max_files:
            shutil.rmtree(repo_dir, ignore_errors=True)
            raise RepoLimitExceededError(
                f"Repository exceeds file limit ({max_files:,} files)."
            )

        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                # Do not follow symlinks
                stat_res = os.lstat(filepath)
                total_size += stat_res.st_size
            except OSError:
                continue

            if total_size > max_bytes:
                shutil.rmtree(repo_dir, ignore_errors=True)
                raise RepoLimitExceededError(
                    f"Repository exceeds size limit ({settings.MAX_REPO_SIZE_MB} MB)."
                )


def detect_default_branch(repo_dir: Path) -> str:
    """
    Detect the default branch of the cloned repository.
    """
    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        return "main"

    try:
        res = subprocess.run(
            [
                "git",
                "--git-dir",
                str(git_dir),
                "--work-tree",
                str(repo_dir),
                "branch",
                "--show-current",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        branch = res.stdout.strip()
        if branch:
            return branch
    except Exception:
        pass

    try:
        res = subprocess.run(
            [
                "git",
                "--git-dir",
                str(git_dir),
                "--work-tree",
                str(repo_dir),
                "symbolic-ref",
                "--short",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        branch = res.stdout.strip()
        if branch:
            return branch
    except Exception:
        pass

    return "main"


def ingest_repository(db: Session, raw_github_url: str) -> Repository:
    """
    Execute repository ingestion pipeline:
    1. Validate GitHub URL and extract owner/repo.
    2. Create / retrieve Repository database record.
    3. Clone into isolated workspace directory.
    4. Enforce size and file limits.
    5. Detect default branch.
    6. Transition status to READY and persist.
    """
    # 1. Validate URL & extract metadata
    clean_url, owner, repo_name = validate_github_url(raw_github_url)
    display_name = f"{owner}/{repo_name}"

    # 2. Check existing record
    existing = db.query(Repository).filter(Repository.github_url == clean_url).first()

    if existing:
        if existing.status == RepositoryStatus.READY:
            raise RepositoryAlreadyExistsError(
                f"Repository '{display_name}' has already been ingested."
            )
        if existing.status == RepositoryStatus.INDEXING:
            raise RepositoryAlreadyExistsError(
                f"Repository '{display_name}' is currently being ingested."
            )
        # If status was failed, allow re-ingestion
        repo = existing
        repo.status = RepositoryStatus.PENDING
        repo.name = display_name
        db.commit()
        db.refresh(repo)
    else:
        repo = Repository(
            name=display_name,
            github_url=clean_url,
            default_branch="main",
            status=RepositoryStatus.PENDING,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    # 3. Mark status as INDEXING
    repo.status = RepositoryStatus.INDEXING
    db.commit()
    db.refresh(repo)

    target_dir = get_repo_storage_path(repo.id)

    # 4. Perform controlled clone and validation
    try:
        clone_repository(clean_url, target_dir)
        validate_repo_limits(target_dir)
        branch = detect_default_branch(target_dir)

        # 5. Scan repository and create file inventory
        scan_repository_files(db, repo.id, target_dir)

        repo.default_branch = branch
        repo.status = RepositoryStatus.READY
        db.commit()
        db.refresh(repo)
        return repo
    except Exception as exc:
        shutil.rmtree(target_dir, ignore_errors=True)
        repo.status = RepositoryStatus.FAILED
        db.commit()
        db.refresh(repo)
        logger.error("Repository ingestion failed for %s: %s", clean_url, exc)
        raise

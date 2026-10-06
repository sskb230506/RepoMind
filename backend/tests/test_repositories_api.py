from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from backend.app.main import app
    from backend.app.models.repository import Repository, RepositoryStatus
    from backend.app.models.repository_file import RepositoryFile
    from backend.app.services.ingestion import GitCloneError
except ModuleNotFoundError:
    from app.main import app
    from app.models.repository import Repository, RepositoryStatus
    from app.models.repository_file import RepositoryFile
    from app.services.ingestion import GitCloneError

client = TestClient(app)


class TestRepositoriesApi:
    """Integration test suite for POST /api/repositories and repository inspection."""

    @patch("backend.app.services.ingestion.clone_repository")
    @patch("backend.app.services.ingestion.detect_default_branch", return_value="main")
    def test_post_repository_success(
        self,
        mock_branch,
        mock_clone,
        db_session: Session,
        override_get_db,
    ):
        """Test successful repository ingestion via POST /api/repositories."""
        payload = {"github_url": "https://github.com/encode/uvicorn"}
        response = client.post("/api/repositories", json=payload)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == "encode/uvicorn"
        assert data["github_url"] == "https://github.com/encode/uvicorn"
        assert data["default_branch"] == "main"
        assert data["status"] == "ready"
        assert "created_at" in data
        assert "updated_at" in data

        # Security requirement: Never expose server filesystem paths
        data_str = str(data)
        assert "repo_" not in data_str
        assert (
            "repositories" not in data_str or data_str.count("repositories") == 0
        )  # only in url if any
        assert "data" not in data
        assert "storage" not in data_str
        assert "/" in data["name"]

    @patch("backend.app.services.ingestion.clone_repository")
    @patch("backend.app.services.ingestion.detect_default_branch", return_value="main")
    def test_post_repository_duplicate_conflict(
        self,
        mock_branch,
        mock_clone,
        db_session: Session,
        override_get_db,
    ):
        """Test that duplicate repository returns 409 Conflict."""
        payload = {"github_url": "https://github.com/encode/starlette"}
        res1 = client.post("/api/repositories", json=payload)
        assert res1.status_code == 201

        res2 = client.post("/api/repositories", json=payload)
        assert res2.status_code == 409
        assert "already been ingested" in res2.json()["detail"]

    def test_post_repository_invalid_url(self, override_get_db):
        """Test invalid GitHub URLs return 400 Bad Request."""
        # Non-github domain
        res = client.post(
            "/api/repositories",
            json={"github_url": "https://gitlab.com/user/project"},
        )
        assert res.status_code == 400
        assert "Only 'github.com' is allowed" in res.json()["detail"]

        # Path traversal
        res = client.post(
            "/api/repositories",
            json={"github_url": "https://github.com/../malicious"},
        )
        assert res.status_code == 400

    @patch(
        "backend.app.services.ingestion.clone_repository",
        side_effect=GitCloneError("Remote repository not found"),
    )
    def test_post_repository_clone_failure(
        self,
        mock_clone,
        db_session: Session,
        override_get_db,
    ):
        """Test git clone failure returns 502 Bad Gateway and records failure."""
        payload = {"github_url": "https://github.com/nonexistent/repo12345"}
        response = client.post("/api/repositories", json=payload)

        assert response.status_code == 502
        assert "Unable to clone repository" in response.json()["detail"]

    @patch("backend.app.services.ingestion.clone_repository")
    @patch("backend.app.services.ingestion.detect_default_branch", return_value="main")
    def test_list_and_get_repositories(
        self,
        mock_branch,
        mock_clone,
        db_session: Session,
        override_get_db,
    ):
        """Test GET /api/repositories and GET /api/repositories/{id}."""
        # Ingest one repo
        res = client.post(
            "/api/repositories",
            json={"github_url": "https://github.com/pallets/click"},
        )
        assert res.status_code == 201
        repo_id = res.json()["id"]

        # List all
        list_res = client.get("/api/repositories")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(item["id"] == repo_id for item in items)

        # Get by ID
        get_res = client.get(f"/api/repositories/{repo_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "pallets/click"

        # Get non-existent
        not_found = client.get("/api/repositories/999999")
        assert not_found.status_code == 404

    def test_get_repository_files_pagination_and_filters(
        self,
        db_session: Session,
        override_get_db,
    ):
        """Test GET /api/repositories/{id}/files with pagination and filters."""
        # 1. Create a repository record
        repo = Repository(
            name="pallets/jinja",
            github_url="https://github.com/pallets/jinja",
            default_branch="main",
            status=RepositoryStatus.READY,
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)

        # 2. Add multiple repository files
        sample_files = [
            RepositoryFile(
                repository_id=repo.id,
                path="src/jinja/environment.py",
                filename="environment.py",
                extension=".py",
                language="Python",
                size_bytes=12000,
                is_binary=False,
                is_generated=False,
            ),
            RepositoryFile(
                repository_id=repo.id,
                path="src/jinja/compiler.py",
                filename="compiler.py",
                extension=".py",
                language="Python",
                size_bytes=8500,
                is_binary=False,
                is_generated=False,
            ),
            RepositoryFile(
                repository_id=repo.id,
                path="src/jinja/runtime.py",
                filename="runtime.py",
                extension=".py",
                language="Python",
                size_bytes=4200,
                is_binary=False,
                is_generated=False,
            ),
            RepositoryFile(
                repository_id=repo.id,
                path="docs/index.md",
                filename="index.md",
                extension=".md",
                language="Markdown",
                size_bytes=1500,
                is_binary=False,
                is_generated=False,
            ),
            RepositoryFile(
                repository_id=repo.id,
                path="assets/logo.png",
                filename="logo.png",
                extension=".png",
                language=None,
                size_bytes=34000,
                is_binary=True,
                is_generated=False,
            ),
            RepositoryFile(
                repository_id=repo.id,
                path="dist/bundle.min.js",
                filename="bundle.min.js",
                extension=".js",
                language="JavaScript",
                size_bytes=52000,
                is_binary=False,
                is_generated=True,
            ),
        ]
        db_session.add_all(sample_files)
        db_session.commit()

        # 3. Test pagination (page=1, page_size=2)
        res_page1 = client.get(f"/api/repositories/{repo.id}/files?page=1&page_size=2")
        assert res_page1.status_code == 200
        data1 = res_page1.json()
        assert data1["total"] == 6
        assert data1["page"] == 1
        assert data1["page_size"] == 2
        assert data1["total_pages"] == 3
        assert len(data1["items"]) == 2

        # Test pagination (page=2, page_size=2)
        res_page2 = client.get(f"/api/repositories/{repo.id}/files?page=2&page_size=2")
        assert res_page2.status_code == 200
        data2 = res_page2.json()
        assert data2["page"] == 2
        assert len(data2["items"]) == 2

        # 4. Test language filter
        res_lang = client.get(f"/api/repositories/{repo.id}/files?language=Python")
        assert res_lang.status_code == 200
        lang_data = res_lang.json()
        assert lang_data["total"] == 3
        assert all(item["language"] == "Python" for item in lang_data["items"])

        # 5. Test is_binary filter
        res_bin = client.get(f"/api/repositories/{repo.id}/files?is_binary=true")
        assert res_bin.status_code == 200
        bin_data = res_bin.json()
        assert bin_data["total"] == 1
        assert bin_data["items"][0]["filename"] == "logo.png"

        # 6. Test is_generated filter
        res_gen = client.get(f"/api/repositories/{repo.id}/files?is_generated=true")
        assert res_gen.status_code == 200
        gen_data = res_gen.json()
        assert gen_data["total"] == 1
        assert gen_data["items"][0]["filename"] == "bundle.min.js"

        # 7. Test path_prefix filter
        res_prefix = client.get(f"/api/repositories/{repo.id}/files?path_prefix=src")
        assert res_prefix.status_code == 200
        prefix_data = res_prefix.json()
        assert prefix_data["total"] == 3
        assert all(item["path"].startswith("src/") for item in prefix_data["items"])

        # 8. Test 404 for non-existent repository
        res_404 = client.get("/api/repositories/999999/files")
        assert res_404.status_code == 404

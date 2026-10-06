from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from backend.app.main import app
    from backend.app.services.ingestion import GitCloneError
except ModuleNotFoundError:
    from app.main import app
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

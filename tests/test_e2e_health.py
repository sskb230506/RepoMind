from fastapi.testclient import TestClient

from backend.app.main import app
from worker.app.config import worker_settings

client = TestClient(app)


def test_e2e_backend_health():
    """Verify backend health endpoint produces valid JSON and expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "repomind-backend"
    assert "version" in data


def test_e2e_worker_config():
    """Verify worker config is loaded and compatible with backend settings."""
    assert worker_settings.WORKER_NAME == "repomind-worker"
    assert worker_settings.WORKER_POLL_INTERVAL > 0

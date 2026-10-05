from fastapi.testclient import TestClient

try:
    from backend.app.main import app
except ModuleNotFoundError:
    from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the root /health endpoint returns 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "repomind-backend"
    assert "version" in data
    assert "environment" in data


def test_api_v1_health_endpoint():
    """Test the /api/v1/health endpoint returns 200 and expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "repomind-backend"


def test_root_endpoint():
    """Test the root / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["health"] == "/health"

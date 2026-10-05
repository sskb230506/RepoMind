import pytest

try:
    from worker.app.config import worker_settings
    from worker.app.main import RepoMindWorker
except ModuleNotFoundError:
    from app.config import worker_settings
    from app.main import RepoMindWorker


def test_worker_settings():
    """Verify default worker configuration."""
    assert worker_settings.WORKER_NAME == "repomind-worker"
    assert worker_settings.WORKER_POLL_INTERVAL >= 1
    assert "postgresql" in worker_settings.DATABASE_URL


@pytest.mark.anyio
async def test_worker_lifecycle():
    """Verify worker starts and stops gracefully."""
    worker = RepoMindWorker()
    assert not worker.is_running

    # Signal stop before or right after start
    worker.stop()
    await worker.start()
    assert not worker.is_running

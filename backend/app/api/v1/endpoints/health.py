from typing import Any

from fastapi import APIRouter

try:
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.core.config import settings

router = APIRouter()


@router.get("", summary="Health Check", response_model=dict[str, Any])
def get_health() -> dict[str, Any]:
    """
    Return operational status of the RepoMind backend service.
    """
    return {
        "status": "healthy",
        "service": "repomind-backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

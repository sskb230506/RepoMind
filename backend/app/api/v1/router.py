from fastapi import APIRouter

try:
    from backend.app.api.v1.endpoints import health, repositories
except ModuleNotFoundError:
    from app.api.v1.endpoints import health, repositories

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["repositories"]
)

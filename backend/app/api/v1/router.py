from fastapi import APIRouter

try:
    from backend.app.api.v1.endpoints import health
except ModuleNotFoundError:
    from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])

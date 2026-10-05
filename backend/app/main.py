from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.api.v1.router import api_router
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.api.v1.router import api_router
    from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RepoMind - AI Codebase Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", tags=["health"], summary="Health Check")
def health_check() -> dict[str, Any]:
    """
    Return a simple JSON response indicating that the backend is running.
    """
    return {
        "status": "healthy",
        "service": "repomind-backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Include versioned API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }

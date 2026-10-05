# RepoMind API Documentation

## Overview

RepoMind provides a RESTful API powered by FastAPI. Interactive OpenAPI documentation is automatically available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## Base URLs

- **Local Development**: `http://localhost:8000`
- **API Version 1 Prefix**: `/api/v1`

---

## Endpoints

### 1. Health Check

Verifies backend operational status and service metadata.

- **URL**: `/health`
- **Method**: `GET`
- **Authentication**: None required
- **Response Codes**:
  - `200 OK`: Service is healthy.

#### Example Request
```bash
curl -X GET http://localhost:8000/health
```

#### Example Response
```json
{
  "status": "healthy",
  "service": "repomind-backend",
  "version": "0.1.0",
  "environment": "development"
}
```

---

### 2. API v1 Health Check

Dedicated versioned health check endpoint.

- **URL**: `/api/v1/health`
- **Method**: `GET`
- **Response**: Same format as `/health`.

---

## Future Endpoints (Roadmap)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| `POST` | `/api/v1/repositories` | Connect a GitHub repository | Planned |
| `GET`  | `/api/v1/repositories` | List connected repositories | Planned |
| `GET`  | `/api/v1/repositories/{id}/graph` | Retrieve dependency graph | Planned |
| `POST` | `/api/v1/repositories/{id}/impact` | Compute change-impact analysis | Planned |

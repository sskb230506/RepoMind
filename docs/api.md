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

### 3. Ingest Repository

Ingests a public GitHub repository into an isolated, secure workspace directory.

- **URL**: `/api/repositories` (also accessible via `/api/v1/repositories`)
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "github_url": "https://github.com/owner/repository"
  }
  ```
- **Response Codes**:
  - `201 Created`: Repository successfully created, cloned, and validated.
  - `400 Bad Request`: Malformed or unsupported URL, or limits exceeded.
  - `409 Conflict`: Repository has already been registered or is currently being ingested.
  - `502 Bad Gateway`: Git clone failure.

#### Example Response
```json
{
  "id": 1,
  "name": "owner/repository",
  "github_url": "https://github.com/owner/repository",
  "default_branch": "main",
  "status": "ready",
  "created_at": "2026-10-06T08:00:00Z",
  "updated_at": "2026-10-06T08:00:05Z"
}
```

---

### 4. List Repositories

- **URL**: `/api/repositories`
- **Method**: `GET`
- **Query Parameters**:
  - `skip` (optional, default: 0)
  - `limit` (optional, default: 100)
- **Response**: Array of repository objects.

---

### 5. Get Repository by ID

- **URL**: `/api/repositories/{id}`
- **Method**: `GET`
- **Response**: Repository object.

---

## Future Endpoints (Roadmap)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| `GET`  | `/api/v1/repositories/{id}/graph` | Retrieve dependency graph | Planned |
| `POST` | `/api/v1/repositories/{id}/impact` | Compute change-impact analysis | Planned |

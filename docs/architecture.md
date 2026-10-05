# RepoMind Architecture Overview

## 1. System Mission

RepoMind is an **AI Codebase Intelligence platform** designed to provide deep structural understanding, dependency tracing, change-impact analysis, and Git history exploration for modern software repositories.

> **Current Phase Note**: In this initial foundation phase, core services, database connections, background workers, and health endpoints are established. AI/RAG/Agent capabilities will be integrated in subsequent milestones.

---

## 2. Monorepo Organization

```
repomind/
├── backend/           # FastAPI REST API, database models, session management
├── frontend/          # React + Vite + TypeScript + Tailwind CSS UI
├── worker/            # Python background worker for repository indexing
├── tests/             # Cross-service integration & end-to-end test suite
├── docs/              # Architectural, API, and setup documentation
├── scripts/           # Local development, setup, and linting scripts
├── docker/            # Service-specific Dockerfiles & container configs
├── docker-compose.yml # Local orchestration for Postgres, Backend, Worker, Frontend
├── .env.example       # Central environment template
├── .gitignore         # Monorepo ignore rules
└── README.md          # Project overview & quickstart guide
```

---

## 3. High-Level Architecture

```
                    ┌─────────────────────────┐
                    │      React Client       │
                    │   (Vite + Tailwind)     │
                    └────────────┬────────────┘
                                 │ HTTP / JSON
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Backend     │
                    │  (/health, /api/v1/...) │
                    └──────┬───────────┬──────┘
                           │           │
            SQLAlchemy ORM │           │ Async Event / Tasks
                           ▼           ▼
        ┌──────────────────────┐   ┌──────────────────────────┐
        │  PostgreSQL Database │   │      Python Worker       │
        │  (Repositories,      │◄──┤  (Background Processing, │
        │   Metadata, Index)   │   │   Git Ingestion, Tasks)  │
        └──────────────────────┘   └──────────────────────────┘
```

---

## 4. Component Boundaries & Responsibilities

### 4.1 Backend (`backend/`)
- **Technology**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Pydantic Settings.
- **Responsibilities**:
  - Exposes RESTful API endpoints (`/health`, `/api/v1/repositories`, etc.).
  - Manages database sessions, connection pooling, and Alembic migrations (`alembic/versions/`).
  - Implements the core domain models: `Repository` with lifecycle statuses (`pending`, `indexing`, `ready`, `failed`).
  - Manages database sessions, connection pooling, and migrations.
  - Enforces authentication, authorization, and tenant isolation (future phase).
  - Validates and coordinates asynchronous jobs with the background worker.

### 4.2 Frontend (`frontend/`)
- **Technology**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Responsibilities**:
  - Delivers an intuitive, sleek dashboard for repository management and intelligence visualization.
  - Monitors system health across backend and background workers.
  - Provides codebase navigation, file browsing, and dependency graph visualization (future phase).

### 4.3 Background Worker (`worker/`)
- **Technology**: Python 3.11+, SQLAlchemy, Asyncio.
- **Responsibilities**:
  - Executes long-running tasks asynchronously away from the HTTP request-response cycle.
  - Future tasks include repository cloning, AST parsing, symbol extraction, Git commit history walking, and test discovery.

### 4.4 PostgreSQL Database
- Persistent relational store for repository metadata, analysis runs, dependency relations, and system state.

---

## 5. Design Decisions

1. **Explicit Monorepo**: Consolidates all services under a single repository for synchronized versioning, simplified atomic commits, and centralized issue tracking.
2. **Environment-Driven Configuration**: Every service is configured using standard environment variables (12-Factor App methodology) with robust typing and validation via Pydantic Settings in Python.
3. **Container-Native**: All services include production-ready Dockerfiles and a unified `docker-compose.yml` for seamless multi-platform local development and CI/CD testing.

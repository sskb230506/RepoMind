# RepoMind

<div align="center">

![RepoMind Platform](https://img.shields.io/badge/RepoMind-Codebase%20Intelligence-8b5cf6?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React%2018-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ruff](https://img.shields.io/badge/Linter-Ruff-black?style=for-the-badge)

<p align="center">
  <strong>An AI Codebase Intelligence Platform engineered to understand, trace, and evolve complex software systems.</strong>
</p>

</div>

---

## 📌 Vision & Roadmap

The long-term goal of **RepoMind** is to empower developers to connect a GitHub repository and:
- 🔍 **Ask Questions** about the architecture, execution paths, and modules.
- 🕸️ **Trace Dependencies** across cross-file imports, symbols, and call graphs.
- 💥 **Perform Change-Impact Analysis** to quantify PR blast radiuses prior to merge.
- 📜 **Inspect Git History** to analyze code churn, hotspots, and author ownership evolution.
- 🧪 **Find Relevant Tests** dynamically mapped to modified code units.
- 🤖 **Agentic Code Synthesis** to propose and validate refactors via autonomous sandboxed agents.

> **Current Foundation Phase**: In this milestone, we establish the core monorepo architecture, FastAPI REST API, PostgreSQL database models/sessions, Python background worker, React + Vite frontend, container orchestration, and health check endpoints. AI, RAG, and Agent integrations will be implemented in subsequent phases.

---

## 📂 Monorepo Structure

```
repomind/
├── backend/                  # FastAPI REST API, database session & models
│   ├── app/
│   │   ├── api/              # API router & versioned endpoints (/health)
│   │   ├── core/             # Configuration & Pydantic settings
│   │   ├── db/               # SQLAlchemy engine & session factory
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # Backend unit tests
│   ├── pyproject.toml        # Ruff & Pytest configuration
│   └── requirements.txt      # Production & development dependencies
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # UI components (Navbar, Hero, HealthStatus, etc.)
│   │   ├── App.tsx           # Main application view with live health monitoring
│   │   ├── index.css         # Tailwind directives & design tokens
│   │   └── main.tsx          # Application root
│   ├── package.json          # Node dependencies and scripts
│   ├── tsconfig.json         # TypeScript configuration
│   ├── tailwind.config.js    # Tailwind styling config
│   └── vite.config.ts        # Vite build & proxy configuration
├── worker/                   # Python background worker service
│   ├── app/
│   │   ├── config.py         # Worker settings & database connection
│   │   └── main.py           # Polling loop & graceful shutdown handlers
│   ├── tests/                # Worker lifecycle tests
│   ├── pyproject.toml        # Worker project metadata
│   └── requirements.txt      # Worker dependencies
├── tests/                    # Cross-service integration & E2E tests
│   ├── conftest.py           # Shared test fixtures & path configuration
│   └── test_e2e_health.py    # E2E health validation test
├── docs/                     # Technical specifications & documentation
│   ├── architecture.md       # Monorepo topology & component boundaries
│   ├── api.md                # API endpoints and schema reference
│   └── setup.md              # Detailed developer onboarding guide
├── scripts/                  # Cross-platform development scripts
│   ├── setup.bat / setup.sh  # Automated monorepo dependency installer
│   ├── run-dev.bat / .sh     # Concurrent local development runner
│   ├── lint.bat / lint.sh    # Ruff and TypeScript verification
│   └── test.bat / test.sh    # Unified test runner across all test suites
├── docker/                   # Docker container definitions
│   ├── backend.Dockerfile    # Multi-stage Python FastAPI container
│   ├── frontend.Dockerfile   # Multi-stage Node build & Nginx runtime
│   ├── worker.Dockerfile     # Python background worker container
│   └── nginx.conf            # Nginx reverse proxy configuration
├── docker-compose.yml        # Docker compose orchestration
├── .env.example              # Centralized environment variable template
├── .gitignore                # Comprehensive ignore rules
└── README.md                 # Project README
```

---

## 🚀 Quick Start

### Option A: Running with Docker Compose (Recommended)

Start the entire system (PostgreSQL, Backend, Worker, Frontend) with a single command:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and launch services
docker compose up --build
```

**Services will be available at:**
- 🌐 **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- 🔌 **Backend API**: [http://localhost:8000](http://localhost:8000)
- 📖 **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Local Development

#### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/sskb230506/RepoMind.git
cd RepoMind

# Copy environment variables
cp .env.example .env
```

#### 2. Run Automated Setup Script
- **Windows**: `scripts\setup.bat`
- **Linux / macOS**: `./scripts/setup.sh`

#### 3. Run Development Servers
- **Windows**: `scripts\run-dev.bat`
- **Linux / macOS**: `./scripts/run-dev.sh`

Or launch them individually:

**Backend:**
```bash
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Worker:**
```bash
source .venv/bin/activate
python -m worker.app.main
```

---

## 🩺 Health Endpoint Specification

RepoMind exposes a health check endpoint to verify backend operational readiness.

### Request
```bash
curl -X GET http://localhost:8000/health
```

### Response (`200 OK`)
```json
{
  "status": "healthy",
  "service": "repomind-backend",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## 🧪 Testing & Linting

### Run All Tests
```bash
# Windows
scripts\test.bat

# Linux / macOS
./scripts/test.sh

# Or via pytest directly
pytest backend/tests/ worker/tests/ tests/
```

### Run Code Quality & Linter Checks
```bash
# Windows
scripts\lint.bat

# Linux / macOS
./scripts/lint.sh

# Or individually
ruff check backend worker tests
ruff format --check backend worker tests
cd frontend && npm run build
```

---

## 🛡️ License

This project is licensed under the Apache 2.0 License.

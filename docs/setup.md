# RepoMind Local Development Setup

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18+ (Node 20+ LTS recommended)
- **Docker & Docker Compose**: (Optional, for containerized workflows)
- **Git**

---

## 1. Quick Start with Docker Compose

The fastest way to spin up the entire monorepo stack:

```bash
# 1. Clone the repository
git clone https://github.com/sskb230506/RepoMind.git
cd RepoMind

# 2. Copy the environment configuration
cp .env.example .env

# 3. Start all services (PostgreSQL, Backend, Worker, Frontend)
docker-compose up --build
```

Access services:
- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 2. Local Manual Setup

### 2.1 Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Run the backend server
uvicorn backend.app.main:app --reload --port 8000
```

### 2.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 2.3 Worker Setup
```bash
# Ensure virtual environment is activated
pip install -r worker/requirements.txt
python -m worker.app.main
```

---

## 3. Running Tests and Linters

### Backend Tests
```bash
pytest backend/tests/
```

### Integration Tests
```bash
pytest tests/
```

### Python Linting (Ruff)
```bash
ruff check .
ruff format --check .
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run build
```

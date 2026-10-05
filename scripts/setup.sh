#!/usr/bin/env bash
set -e

echo "========================================================"
echo " RepoMind Monorepo Setup (Linux / macOS)"
echo "========================================================"

# 1. Python virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "[1/3] Virtual environment already exists (.venv)"
fi

echo "[2/3] Installing Python dependencies (backend, worker)..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r worker/requirements.txt

# 2. Frontend
echo "[3/3] Installing Frontend dependencies (npm)..."
cd frontend
npm install
cd ..

if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
fi

echo ""
echo "========================================================"
echo " RepoMind setup complete!"
echo " To run backend: uvicorn backend.app.main:app --reload"
echo " To run frontend: cd frontend && npm run dev"
echo "========================================================"

#!/usr/bin/env bash
set -e

echo "========================================================"
echo " RepoMind - Running Development Servers"
echo "========================================================"

source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait

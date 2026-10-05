#!/usr/bin/env bash
set -e

echo "========================================================"
echo " RepoMind - Linting and Code Formatting Checks"
echo "========================================================"

echo "[1/2] Checking Python code (Ruff)..."
source .venv/bin/activate
ruff check backend worker tests
ruff format --check backend worker tests

echo "[2/2] Checking Frontend code (TypeScript)..."
cd frontend
npm run build
cd ..

echo ""
echo "All lint and build checks passed successfully!"

#!/usr/bin/env bash
set -e

echo "========================================================"
echo " RepoMind - Running Test Suites"
echo "========================================================"

source .venv/bin/activate

echo "[1/3] Backend Unit Tests..."
pytest backend/tests

echo "[2/3] Worker Tests..."
pytest worker/tests

echo "[3/3] Root E2E Integration Tests..."
pytest tests

echo ""
echo "========================================================"
echo " All test suites passed successfully!"
echo "========================================================"

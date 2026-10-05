@echo off
echo ========================================================
echo  RepoMind Monorepo Setup (Windows)
echo ========================================================

REM 1. Setup Python Virtual Environment
if not exist ".venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv .venv
) else (
    echo [1/3] Virtual environment already exists (.venv)
)

echo [2/3] Installing Python dependencies (backend, worker, tests)...
call .\.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
pip install -r worker\requirements.txt

REM 2. Setup Frontend
echo [3/3] Installing Frontend dependencies (Node / npm)...
cd frontend
call npm install
cd ..

if not exist ".env" (
    echo Copying .env.example to .env...
    copy .env.example .env
)

echo.
echo ========================================================
echo  RepoMind setup complete!
echo  To run backend: uvicorn backend.app.main:app --reload
echo  To run frontend: cd frontend && npm run dev
echo ========================================================

@echo off
echo ========================================================
echo  RepoMind - Running Development Environment
echo ========================================================

start "RepoMind Backend" cmd /k "call .\.venv\Scripts\activate.bat && uvicorn backend.app.main:app --reload --port 8000"
start "RepoMind Frontend" cmd /k "cd frontend && npm run dev"

echo Backend starting on http://localhost:8000
echo Frontend starting on http://localhost:5173
echo Press any key to exit this launcher window...
pause >nul

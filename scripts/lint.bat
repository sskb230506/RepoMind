@echo off
echo ========================================================
echo  RepoMind - Linting and Code Formatting Checks
echo ========================================================

echo [1/2] Checking Python code (Ruff)...
call .\.venv\Scripts\activate.bat
ruff check backend worker tests
if %errorlevel% neq 0 (
    echo Ruff check failed!
    exit /b %errorlevel%
)
ruff format --check backend worker tests
if %errorlevel% neq 0 (
    echo Ruff format check failed!
    exit /b %errorlevel%
)

echo [2/2] Checking Frontend code (TypeScript)...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo Frontend build / typecheck failed!
    exit /b %errorlevel%
)
cd ..

echo.
echo All lint and build checks passed successfully!

@echo off
echo ========================================================
echo  RepoMind - Running Test Suites
echo ========================================================

call .\.venv\Scripts\activate.bat

echo [1/3] Backend Unit Tests...
pytest backend/tests
if %errorlevel% neq 0 exit /b %errorlevel%

echo [2/3] Worker Tests...
pytest worker/tests
if %errorlevel% neq 0 exit /b %errorlevel%

echo [3/3] Root E2E Integration Tests...
pytest tests
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo ========================================================
echo  All 3 test suites passed successfully!
echo ========================================================

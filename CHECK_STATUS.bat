@echo off
echo ========================================
echo   RAG Chatbot - Status Check
echo ========================================
echo.

echo Checking Backend (port 8000)...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Backend is RUNNING at http://localhost:8000
) else (
    echo [ERROR] Backend is NOT running
)
echo.

echo Checking Frontend (port 3000)...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Frontend is RUNNING at http://localhost:3000
) else (
    echo [WARNING] Frontend may still be starting...
)
echo.

echo ========================================
echo   Ready to use!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo.
echo Open http://localhost:3000 in your browser
echo.
pause


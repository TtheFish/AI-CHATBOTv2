@echo off
title RAG Chatbot - Start All Services
color 0E
cls
echo ========================================
echo   RAG Chatbot - Starting All Services
echo ========================================
echo.
echo This will start both backend and frontend
echo.
echo Press any key to start...
pause >nul
echo.

echo [1/2] Starting Backend Server...
start "RAG Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend...
start "RAG Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ========================================
echo   Services Starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Two windows will open - keep them running!
echo.
echo Waiting 15 seconds for services to start...
timeout /t 15 /nobreak >nul

echo.
echo Checking status...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Backend is running
) else (
    echo [WARNING] Backend may still be starting...
)

echo.
echo ========================================
echo   Ready to use!
echo ========================================
echo.
echo Open your browser and go to:
echo http://localhost:3000
echo.
pause


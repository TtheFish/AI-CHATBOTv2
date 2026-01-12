@echo off
title RAG Chatbot Backend Server
color 0A
echo ========================================
echo   RAG Chatbot Backend Server
echo ========================================
echo.
cd /d "%~dp0backend"
echo Current directory: %CD%
echo.
echo Starting FastAPI server...
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause


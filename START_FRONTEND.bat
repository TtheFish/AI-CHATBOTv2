@echo off
title RAG Chatbot Frontend
color 0B
echo ========================================
echo   RAG Chatbot Frontend
echo ========================================
echo.
cd /d "%~dp0frontend"
echo Current directory: %CD%
echo.
echo Starting React development server...
echo.
call npm start
pause


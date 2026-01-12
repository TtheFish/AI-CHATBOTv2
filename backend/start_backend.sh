#!/bin/bash
echo "Starting RAG Chatbot Backend..."
python -m uvicorn app.main:app --reload --port 8000


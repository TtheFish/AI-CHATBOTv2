# RAG Chatbot Backend

FastAPI backend for RAG (Retrieval-Augmented Generation) chatbot system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
# For OpenAI embeddings and chat (recommended)
export OPENAI_API_KEY="your-api-key-here"

# If not using OpenAI, sentence-transformers will be used as fallback
```

3. Run the server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Health check
- `POST /api/documents/upload` - Upload and process a document (PDF, DOC, DOCX)
- `POST /api/chat/` - Send a chat message and get RAG-powered response
- `GET /api/chat/conversation/{conversation_id}` - Get conversation history

## Notes

- Documents are stored in vector database (ChromaDB) with embeddings
- Supports OpenAI API or sentence-transformers for embeddings
- Chat responses use RAG to retrieve relevant document context


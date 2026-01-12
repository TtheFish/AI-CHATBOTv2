# RAG Chatbot System

A complete RAG (Retrieval-Augmented Generation) system with a chatbot interface. Users can upload documents (PDF, DOC, DOCX) and interact with them through a conversational interface.

## Features

- 📄 **Document Upload**: Support for PDF, DOC, and DOCX files
- 🔍 **Vector Search**: ChromaDB for efficient semantic search
- 🤖 **RAG Chatbot**: Ask questions and get answers based on your documents
- ⚡ **FastAPI Backend**: High-performance async API
- ⚛️ **React Frontend**: Modern, responsive UI
- 📄 **Page-specific Queries**: Ask about specific pages (e.g., "what is on page 5")
- 💬 **ChatGPT-like Interface**: Natural conversation support

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Set OpenAI API key for better embeddings and chat:
```bash
# On Windows PowerShell:
$env:OPENAI_API_KEY="your-api-key-here"

# On Mac/Linux:
export OPENAI_API_KEY="your-api-key-here"
```

**Note**: If you don't set an OpenAI API key, the system will use sentence-transformers as a fallback, which works offline but with slightly lower quality.

5. Run the backend server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Upload a Document**: Click the "Upload Document" button and select a PDF, DOC, or DOCX file
2. **Wait for Processing**: The document will be processed and indexed (this may take a moment)
3. **Start Chatting**: Type questions about your document in the chat interface
4. **Get Answers**: The system will retrieve relevant information from your document and generate responses
5. **Page Queries**: Ask about specific pages (e.g., "what is on page 5", "last page")

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload and process a document
- `GET /api/documents/list` - List processed documents

### Chat
- `POST /api/chat/` - Send a chat message
- `GET /api/chat/conversation/{conversation_id}` - Get conversation history

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework
- **ChromaDB**: Vector database for embeddings
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX text extraction
- **OpenAI API** (optional): For embeddings and chat generation
- **sentence-transformers** (fallback): Local embeddings model

### Frontend
- **React**: UI library
- **Axios**: HTTP client
- **CSS3**: Modern styling

## Notes

- This is an MVP (Minimum Viable Product) version
- Documents are processed and stored in a local ChromaDB instance
- Conversations are stored in memory (not persisted across server restarts)
- For production use, consider:
  - Database for conversation persistence
  - Authentication and authorization
  - Rate limiting
  - Better error handling
  - Document management UI
  - Multi-user support

## Troubleshooting

### Backend Issues
- Ensure all Python dependencies are installed
- Check that port 8000 is not in use
- Verify file permissions for uploads directory

### Frontend Issues
- Ensure Node.js and npm are installed
- Try clearing npm cache: `npm cache clean --force`
- Check that port 3000 is not in use

### Embedding Issues
- If OpenAI API is not available, sentence-transformers will be used automatically
- First run may take longer as models are downloaded

## License

MIT License - feel free to use and modify as needed.

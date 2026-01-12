import os
import uuid
from pathlib import Path
from typing import List, Tuple, Dict
import PyPDF2
import docx
from datetime import datetime

# For embeddings - using OpenAI (can be replaced with other providers)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. Set OPENAI_API_KEY or install openai package.")

# Vector database
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not installed. Install chromadb package.")

# Create uploads directory relative to backend folder
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class DocumentProcessor:
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required. Install it with: pip install chromadb")
        
        # Use PersistentClient for newer ChromaDB versions
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
        except AttributeError:
            # Fallback for older versions
            from chromadb.config import Settings
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db"
            ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents"
        )
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        # Fallback: use sentence transformers if OpenAI not available
        if not self.openai_client:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Using sentence-transformers for embeddings")
            except ImportError:
                print("Warning: No embedding model available. Install openai or sentence-transformers")
                self.embedding_model = None
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI embedding error: {e}, falling back to sentence-transformers")
                if self.embedding_model:
                    return self.embedding_model.encode(text).tolist()
                raise Exception(f"OpenAI failed and no fallback: {e}")
        elif self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        else:
            raise Exception("No embedding model available")
    
    def extract_text_from_pdf(self, file_path: Path) -> Tuple[str, List[Tuple[int, str]]]:
        """Extract text from PDF file with page information
        Returns: (full_text, list of (page_num, page_text))"""
        full_text = ""
        pages_data = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                page_text = page.extract_text()
                full_text += page_text + "\n"
                pages_data.append((page_num, page_text))
        return full_text, pages_data
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
        """Split text into chunks with overlap - larger chunks for better context"""
        # Try to split by paragraphs first for better semantic units
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_words = para.split()
            para_length = len(para_words)
            
            # If paragraph is too large, split it
            if para_length > chunk_size:
                # First, save current chunk if exists
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split large paragraph into smaller chunks
                for i in range(0, para_length, chunk_size - overlap):
                    chunk = " ".join(para_words[i:i + chunk_size])
                    if chunk.strip():
                        chunks.append(chunk)
            else:
                # Check if adding this para would exceed chunk size
                if current_length + para_length > chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Keep overlap - take last few words from previous chunk
                    overlap_words = min(overlap // 10, len(current_chunk))
                    current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                    current_length = len(current_chunk)
                
                # Add paragraph to current chunk
                current_chunk.extend(para_words)
                current_length += para_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Fallback: if no chunks created, use word-based splitting
        if not chunks:
            words = text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk)
        
        return chunks
    
    def process_document(self, file_path: Path, filename: str) -> str:
        """Process a document and store it in the vector database with page information"""
        document_id = str(uuid.uuid4())
        
        # Extract text based on file type
        pages_data = None
        if filename.endswith('.pdf'):
            text, pages_data = self.extract_text_from_pdf(file_path)
        elif filename.endswith(('.doc', '.docx')):
            text = self.extract_text_from_docx(file_path)
            # For DOCX, treat as single "page"
            pages_data = [(1, text)]
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        if not text.strip():
            raise ValueError("No text extracted from document")
        
        # Store pages data for page queries
        if not hasattr(self, '_document_pages'):
            self._document_pages = {}
        self._document_pages[document_id] = pages_data if pages_data else []
        print(f"Stored {len(pages_data) if pages_data else 0} pages for document {document_id}")
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        # Generate embeddings and store in vector DB
        embeddings = []
        ids = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{i}"
            embedding = self.get_embedding(chunk)
            
            # Determine which page this chunk likely belongs to
            page_num = 1
            if pages_data:
                # Find page by checking which page contains most of this chunk
                chunk_lower = chunk.lower()
                best_page = 1
                max_overlap = 0
                for pnum, ptext in pages_data:
                    # Count word overlap
                    chunk_words = set(chunk_lower.split())
                    page_words = set(ptext.lower().split())
                    overlap = len(chunk_words & page_words)
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_page = pnum
                page_num = best_page
            
            embeddings.append(embedding)
            ids.append(chunk_id)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "page_number": page_num,
                "upload_date": datetime.now().isoformat()
            })
            documents.append(chunk)
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
            documents=documents
        )
        
        return document_id
    
    def get_page_content(self, document_id: str, page_num: int) -> str:
        """Get content of a specific page"""
        if not hasattr(self, '_document_pages'):
            print(f"Warning: _document_pages not found")
            return ""
        pages_data = self._document_pages.get(document_id, [])
        print(f"Looking for page {page_num} in document {document_id}, found {len(pages_data)} pages")
        for pnum, ptext in pages_data:
            if pnum == page_num:
                print(f"Found page {page_num}, content length: {len(ptext)}")
                return ptext
        print(f"Page {page_num} not found in document {document_id}")
        return ""
    
    def get_total_pages(self, document_id: str) -> int:
        """Get total number of pages for a document"""
        if not hasattr(self, '_document_pages'):
            return 0
        pages_data = self._document_pages.get(document_id, [])
        return len(pages_data) if pages_data else 0
    
    def search_documents(self, query: str, n_results: int = 10) -> List[Tuple[str, float]]:
        """Search for relevant document chunks with better retrieval"""
        try:
            query_embedding = self.get_embedding(query)
            
            # Get more results than needed, then filter
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 2, 20)  # Get more results for better selection
            )
            
            # Format results: (text, distance)
            retrieved_chunks = []
            if results.get('documents') and len(results['documents'][0]) > 0:
                documents = results['documents'][0]
                distances = results.get('distances', [])[0] if results.get('distances') else [0] * len(documents)
                
                # Pair documents with distances and sort by relevance (lower distance = more relevant)
                chunk_distances = list(zip(documents, distances))
                chunk_distances.sort(key=lambda x: x[1])  # Sort by distance (ascending)
                
                # Return top n_results
                for doc, distance in chunk_distances[:n_results]:
                    retrieved_chunks.append((doc, distance))
            
            return retrieved_chunks
        except Exception as e:
            print(f"Search error: {e}")
            return []


# Global instance - lazy initialization
document_processor = None

def get_document_processor():
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor


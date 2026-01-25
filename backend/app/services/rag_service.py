import os
import google.generativeai as genai
from typing import List, Tuple, Dict, Any
from app.services.document_processor import get_document_processor

class RAGService:
    def __init__(self):
        self._processor = None
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                print("DEBUG: Gemini 2.0 Flash Connected")
            except Exception as e:
                print(f"Gemini Init Error: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
    
    @property
    def document_processor(self):
        if self._processor is None:
            self._processor = get_document_processor()
        return self._processor

    def generate_response(self, query: str, context_chunks: List[str], history: List[Dict[str, str]] = []) -> str:
        """
        Generate response using History + Document Context
        """
        context_str = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant document section found."
        
        # Build Chat History String for Prompt
        chat_history_str = ""
        # Take last 5 messages to avoid token limit, skipping the very last one (which is the current query)
        recent_history = history[-6:-1] if len(history) > 1 else [] 
        
        for msg in recent_history:
            role = "User" if msg['role'] == 'user' else "AI"
            chat_history_str += f"{role}: {msg['content']}\n"

        system_prompt = f"""
        You are a Document Analysis AI. Your primary mission is to answer questions based on the provided document.
        
        [STRICT RULES]
        1. **PRIORITY**: You MUST look for the answer in the [Document Content] first.
        2. **SOURCE TRUTH**: For specific fact-checking, use ONLY the document. 
        3. **CREATIVE TASKS**: If the user asks for summaries, quizzes, or lists (e.g. "10 questions"), you may EXTRAPOLATE from the provided content to generate full results, as long as they are relevant to the document topics.
        4. **LANGUAGE**: You MUST answer in **ENGLISH** only, even if the user asks in Turkish or the document is in Turkish. Translate the information if necessary.
        5. **FALLBACK**: Only if the document is silent on the topic, use your general knowledge, but you MUST state "This is general information, not from the document."
        
        [Conversation History]
        {chat_history_str}
        
        [Document Content]
        {context_str}
        
        [Current User Question]
        {query}
        
        Answer:
        """

        # 1. Gemini
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(system_prompt)
                return response.text
            except Exception as e:
                return f"⚠️ CRM Error: {str(e)}"
        
        # 2. OpenAI Fallback
        processor = self.document_processor
        if processor.openai_client:
            try:
                response = processor.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": system_prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI Error: {e}")

        # 3. No Brain Fallback
        if not context_chunks:
            return "I am in Offline Mode (No AI Key). I can only search specific terms, not chat."
            
        return "Offline Mode - Search Results:\n" + "\n".join(context_chunks[:2])

    def query(self, user_query: str, history: List[Dict[str, str]] = []) -> Tuple[str, List[str]]:
        """
        Stateful Query Handler
        """
        # 1. Simple Greetings Check
        # Removed hardcoded list. The LLM (Gemini) handles greetings naturally.
        
        processor = self.document_processor
        
        # 2. Search Vector DB
        # Dynamic Context Limit: Increase window for broad generation tasks
        broad_keywords = ['summary', 'summarize', 'overview', 'questions', 'quiz', 'list', 'create', 'generate']
        limit = 10 if any(k in user_query.lower() for k in broad_keywords) else 5
        
        results = processor.search_documents(user_query, n_results=limit)
        
        context_chunks = []
        if results:
            context_chunks = [doc for doc, dist in results]
            
        # 3. Generate Logic
        response = self.generate_response(user_query, context_chunks, history)
        
        sources = ["Document"] if context_chunks else ["General Knowledge"]
        return response, sources

rag_service = RAGService()

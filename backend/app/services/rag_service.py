import os
import re
from typing import List, Tuple
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

from app.services.document_processor import get_document_processor


class RAGService:
    def __init__(self):
        self._processor = None
        self.openai_client = None
        
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
    
    @property
    def document_processor(self):
        if self._processor is None:
            self._processor = get_document_processor()
        return self._processor
    
    def extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from query - handle typos, short queries, multi-word terms"""
        query_lower = query.lower().strip()
        
        # Fix common typos
        query_lower = query_lower.replace('deifne', 'define').replace('defien', 'define')
        query_lower = query_lower.replace('waht', 'what').replace('whate', 'what')
        query_lower = query_lower.replace('grapgh', 'graph').replace('grahph', 'graph')
        query_lower = query_lower.replace('comlete', 'complete').replace('complte', 'complete')
        
        # Remove punctuation at end
        query_lower = re.sub(r'[?!.]+$', '', query_lower).strip()
        
        # Remove question words
        stopwords = ['define', 'what', 'is', 'are', 'tell', 'me', 'about', 'explain', 'describe', 
                    'how', 'why', 'when', 'where', 'can', 'you', 'please', 'the', 'a', 'an']
        words = [w for w in query_lower.split() if w not in stopwords and len(w) > 1]
        
        if not words:
            # Fallback: use query as-is minus stopwords
            cleaned = re.sub(r'\b(define|what|is|are|tell|me|about|explain|describe|please|the|a|an)\b', '', query_lower, flags=re.IGNORECASE)
            words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
        
        if not words:
            return [query_lower]  # Last resort
        
        # Build search terms: full phrase first, then individual words
        search_terms = []
        
        # Add full phrase if 2+ words (e.g., "complete path", "complete graph")
        if len(words) >= 2:
            phrase = ' '.join(words)
            search_terms.append(phrase)
        
        # Add individual words
        search_terms.extend(words)
        
        return search_terms
    
    def extract_answer_from_context(self, query: str, context: str) -> str:
        """Extract answer from context - SIMPLE and DIRECT approach"""
        search_terms = self.extract_search_terms(query)
        
        if not search_terms:
            return "I couldn't find specific information about that in the uploaded documents."
        
        primary_term = search_terms[0]
        primary_term_lower = primary_term.lower()
        primary_words = primary_term.split()
        
        # ULTRA SIMPLE: Just find any sentence/paragraph that contains the term
        # Split by sentences and paragraphs
        # First, try to find definition sentences
        definition_keywords = ['is', 'means', 'defined as', 'refers to', 'is a', 'are', 'denotes', 'called']
        
        # Split into sentences
        sentences = []
        parts = re.split(r'([.!?]+\s*)', context)
        for i in range(0, len(parts), 2):
            if i < len(parts):
                sent = parts[i].strip()
                if sent:
                    punct = parts[i+1] if i+1 < len(parts) else '. '
                    sentences.append((sent, punct))
        
        # Strategy 1: Find sentence with term + definition keyword
        for sentence, punct in sentences:
            sentence_lower = sentence.lower()
            
            # Must contain primary term
            has_term = False
            if len(primary_words) == 1:
                if re.search(rf'\b{re.escape(primary_term_lower)}\b', sentence_lower):
                    has_term = True
            else:
                if primary_term_lower in sentence_lower:
                    has_term = True
            
            if not has_term:
                continue
            
            # Must have definition keyword
            has_def = any(kw in sentence_lower for kw in definition_keywords)
            
            if has_def:
                # Found definition! Clean it up
                clean = sentence.strip()
                clean = re.sub(r'^\d+[-.)]\s*', '', clean)
                clean = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean)
                
                # If list sentence, extract only our part
                if ', ' in clean or ' and ' in clean:
                    parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', clean)
                    for part in parts_list:
                        if primary_term_lower in part.lower():
                            if any(kw in part.lower() for kw in definition_keywords):
                                clean = part.strip()
                                break
                
                if len(clean) > 20:
                    return (clean + punct).strip()[:1000]
        
        # Strategy 2: Find ANY sentence with term (even without definition keyword)
        for sentence, punct in sentences:
            sentence_lower = sentence.lower()
            
            # Check if contains term
            if len(primary_words) == 1:
                if not re.search(rf'\b{re.escape(primary_term_lower)}\b', sentence_lower):
                    continue
            else:
                if primary_term_lower not in sentence_lower:
                    continue
            
            if len(sentence) > 20:
                clean = sentence.strip()
                clean = re.sub(r'^\d+[-.)]\s*', '', clean)
                clean = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean)
                
                # Extract from list if needed
                if ', ' in clean:
                    parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', clean)
                    for part in parts_list:
                        if primary_term_lower in part.lower() and len(part.strip()) > 15:
                            clean = part.strip()
                            break
                
                return (clean + punct).strip()[:1000]
        
        # Strategy 3: Find paragraph with term
        paragraphs = re.split(r'\n\s*\n+', context)
        for para in paragraphs:
            para_lower = para.lower()
            if primary_term_lower in para_lower:
                # Get first few sentences
                para_sents = re.split(r'([.!?]+\s*)', para)
                result = []
                for i in range(0, min(6, len(para_sents)), 2):
                    if i < len(para_sents):
                        sent = para_sents[i].strip()
                        if sent and len(sent) > 10:
                            punct = para_sents[i+1] if i+1 < len(para_sents) else '. '
                            result.append(sent + punct)
                            if len(''.join(result)) > 500:
                                break
                
                if result:
                    answer = ''.join(result)
                    answer = re.sub(r'^\d+[-.)]\s*', '', answer)
                    return answer.strip()[:1000]
        
        return "I couldn't find specific information about '{}' in the uploaded documents.".format(query)
        
        for sentence, punct in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains the PRIMARY term
            contains_primary = False
            if len(primary_words) == 1:
                if re.search(rf'\b{re.escape(primary_term_lower)}\b', sentence_lower):
                    contains_primary = True
            else:
                if primary_term_lower in sentence_lower:
                    contains_primary = True
                elif all(word in sentence_lower for word in primary_words):
                    contains_primary = True
            
            if not contains_primary:
                continue
            
            # CRITICAL: Skip if sentence contains excluded terms (other definitions)
            # This prevents "path (as a graph) and cycle..." when asking for "complete graph"
            if exclude_list:
                has_excluded = any(excluded_term in sentence_lower for excluded_term in exclude_list)
                if has_excluded:
                    # Check if it's a list sentence (contains multiple definitions)
                    # Pattern: "term1, term2, term3" or "term1 and term2"
                    if ', ' in sentence_lower or ' and ' in sentence_lower:
                        # It's a list - try to extract only our part
                        # Split by commas and "and"
                        parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', sentence)
                        found_our_part = False
                        for part in parts_list:
                            part_lower = part.lower()
                            # Check if this part is about our primary term
                            if primary_term_lower in part_lower or all(w in part_lower for w in primary_words):
                                # Check if it has definition keyword
                                if any(kw in part_lower for kw in definition_keywords):
                                    # Check if it doesn't have excluded terms
                                    if not any(excluded_term in part_lower for excluded_term in exclude_list):
                                        clean_sent = part.strip()
                                        clean_sent = re.sub(r'^\d+[-.)]\s*', '', clean_sent)
                                        clean_sent = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean_sent)
                                        found_our_part = True
                                        return (clean_sent + punct).strip()[:1000]
                        if found_our_part:
                            # Already returned, but this shouldn't be reached
                            break
                        # If we couldn't extract our part from list, skip this sentence
                        continue
            
            # Check for definition keywords
            has_def_keyword = any(keyword in sentence_lower for keyword in definition_keywords)
            
            if has_def_keyword:
                # Found a definition! Clean it up
                clean_sent = sentence.strip()
                clean_sent = re.sub(r'^\d+[-.)]\s*', '', clean_sent)
                clean_sent = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean_sent)
                clean_sent = re.sub(r'^\d+\s*[-.)]?\s*[Dd]efine\s+', '', clean_sent)
                
                # Extract only our part if it's a list sentence
                if ', ' in clean_sent or ' and ' in clean_sent:
                    parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', clean_sent)
                    for part in parts_list:
                        part_lower = part.lower()
                        if primary_term_lower in part_lower or all(w in part_lower for w in primary_words):
                            if any(kw in part_lower for kw in definition_keywords):
                                clean_sent = part.strip()
                                break
                
                return (clean_sent + punct).strip()[:1000]
        
        # Strategy 2: Find ANY sentence with the term (even without definition keyword) - MORE AGGRESSIVE
        for term in search_terms:
            term_lower = term.lower()
            term_words = term.split()
            
            for sentence, punct in sentences:
                sentence_lower = sentence.lower()
                
                # Check if contains term - try multiple patterns
                contains_term = False
                
                # Pattern 1: Exact phrase match
                if term_lower in sentence_lower:
                    contains_term = True
                # Pattern 2: Word boundary match for single word
                elif len(term_words) == 1:
                    if re.search(rf'\b{re.escape(term_lower)}\b', sentence_lower):
                        contains_term = True
                # Pattern 3: All words present (fuzzy match)
                elif all(word in sentence_lower for word in term_words):
                    contains_term = True
                
                if contains_term:
                    # Skip if it's clearly a list with excluded terms
                    if exclude_list:
                        has_many_excluded = sum(1 for excl in exclude_list if excl in sentence_lower)
                        if has_many_excluded >= 2 and ', ' in sentence_lower:
                            # Try to extract just our part
                            parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', sentence)
                            for part in parts_list:
                                part_lower = part.lower()
                                if (term_lower in part_lower or all(w in part_lower for w in term_words)):
                                    if not any(excl in part_lower for excl in exclude_list):
                                        if len(part.strip()) > 15:
                                            clean_sent = part.strip()
                                            clean_sent = re.sub(r'^\d+[-.)]\s*', '', clean_sent)
                                            clean_sent = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean_sent)
                                            return (clean_sent + punct).strip()[:1000]
                            continue  # Skip this sentence if we couldn't extract our part
                    
                    # Found a sentence with the term - return it if it's substantial
                    if len(sentence) > 15:
                        clean_sent = sentence.strip()
                        clean_sent = re.sub(r'^\d+[-.)]\s*', '', clean_sent)
                        clean_sent = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', clean_sent)
                        
                        # Extract relevant part if it's a list
                        if ', ' in clean_sent and len(term_words) <= 2:
                            parts_list = re.split(r',\s*(?:and\s+)?[aA]n?\s+', clean_sent)
                            for part in parts_list:
                                if term_lower in part.lower() or all(w in part.lower() for w in term_words):
                                    if len(part.strip()) > 15:
                                        clean_sent = part.strip()
                                        break
                        
                        return (clean_sent + punct).strip()[:1000]
        
        # Strategy 3: Find paragraph with the term
        paragraphs = re.split(r'\n\s*\n+', context)
        for term in search_terms:
            term_lower = term.lower()
            term_words = term.split()
            
            for para in paragraphs:
                para_lower = para.lower()
                if term_lower in para_lower or all(word in para_lower for word in term_words):
                    # Found paragraph with term - extract first few sentences
                    para_sents = re.split(r'([.!?]+\s*)', para)
                    result_parts = []
                    for i in range(0, min(6, len(para_sents)), 2):
                        if i < len(para_sents):
                            sent = para_sents[i].strip()
                            if sent and len(sent) > 10:
                                punct = para_sents[i+1] if i+1 < len(para_sents) else '. '
                                result_parts.append(sent + punct)
                                if len(''.join(result_parts)) > 500:
                                    break
                    
                    if result_parts:
                        answer = ''.join(result_parts)
                        answer = re.sub(r'^\d+[-.)]\s*', '', answer)
                        answer = re.sub(r'^[A-Z0-9]+[-.)]\s*', '', answer)
                        return answer.strip()[:1000]
        
        return "I couldn't find specific information about '{}' in the uploaded documents. Please try rephrasing your question.".format(query)
    
    def generate_response(self, query: str, context_chunks: List[str], use_rag: bool = True) -> str:
        """Generate response - uses OpenAI if available, otherwise FREE method"""
        if not use_rag or not context_chunks:
            return "Please upload a document first to ask questions about it. This is a document-based RAG chatbot."
        
        # If OpenAI is available and configured, use it
        if self.openai_client:
            try:
                context = "\n\n---\n\n".join(context_chunks)
                prompt = f"""Answer this question based ONLY on the document content below. Be specific and direct.

Question: "{query}"

Document Content:
{context}

Answer only what was asked. If asking for a definition, provide the definition from the document:"""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided document context."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI error, using free method: {e}")
        
        # FREE METHOD - Combine all chunks and extract answer
        combined_context = "\n\n---\n\n".join(context_chunks)
        answer = self.extract_answer_from_context(query, combined_context)
        
        # Clean up answer - remove duplicate sentences
        if answer and "couldn't find" not in answer.lower():
            sentences = re.split(r'([.!?]+\s*)', answer)
            seen = set()
            cleaned = []
            for i in range(0, len(sentences), 2):
                if i < len(sentences):
                    sent = sentences[i].strip()
                    key = sent.lower()[:100]
                    if key and key not in seen and len(sent) > 10:
                        seen.add(key)
                        punct = sentences[i+1] if i+1 < len(sentences) else '. '
                        cleaned.append(sent + punct)
            
            if cleaned:
                answer = ''.join(cleaned)
            
            # Limit length
            if len(answer) > 800:
                truncated = answer[:800]
                last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
                if last_punct > 400:
                    answer = answer[:last_punct + 1]
                else:
                    answer = answer[:800] + "..."
        
        return answer if answer else "I couldn't find specific information about that in the uploaded documents."
    
    def has_documents(self) -> bool:
        """Check if there are any documents in the collection"""
        try:
            processor = self.document_processor
            try:
                count = processor.collection.count()
                return count > 0
            except AttributeError:
                try:
                    peek = processor.collection.peek(limit=1)
                    return len(peek.get('ids', [])) > 0
                except:
                    return False
        except Exception as e:
            print(f"Error checking documents: {e}")
            return False
    
    def handle_page_query(self, query_lower: str) -> Tuple[str, bool]:
        """Handle page-related queries - SIMPLIFIED and ROBUST"""
        processor = self.document_processor
        
        # Check for page query patterns
        page_num = None
        page_type = None
        
        # Pattern 1: "what is on page X" or "what's on page X"
        match = re.search(r'what\s+(?:is|are)\s+on\s+page\s+(\d+)', query_lower)
        if not match:
            match = re.search(r'what\'?s\s+on\s+page\s+(\d+)', query_lower)
        if match:
            page_num = int(match.group(1))
            page_type = 'number'
        
        # Pattern 2: "last page" or "give me the last page"
        if not page_num:
            if re.search(r'last\s+page', query_lower):
                page_type = 'last'
            elif re.search(r'first\s+page', query_lower):
                page_type = 'first'
            elif re.search(r'page\s+(\d+)', query_lower):
                match = re.search(r'page\s+(\d+)', query_lower)
                page_num = int(match.group(1))
                page_type = 'number'
        
        if not page_type:
            return "", False
        
        # Get page content
        try:
            # Get document ID
            sample = processor.collection.peek(limit=100)
            if not sample.get('ids'):
                return "", False
            
            doc_ids = set()
            if sample.get('metadatas'):
                for meta in sample['metadatas']:
                    if 'document_id' in meta:
                        doc_ids.add(meta['document_id'])
            
            if not doc_ids:
                return "", False
            
            doc_id = list(doc_ids)[0]
            
            # Get all data to find page chunks
            all_data = processor.collection.get()
            if not all_data or not all_data.get('documents'):
                return "", False
            
            metadatas = all_data.get('metadatas', [])
            documents = all_data['documents']
            
            # Determine page number
            if page_type == 'last':
                # Find max page number
                max_page = 0
                for meta in metadatas:
                    pnum = meta.get('page_number', 0)
                    if isinstance(pnum, (int, str)):
                        try:
                            pnum = int(pnum)
                            if pnum > max_page:
                                max_page = pnum
                        except:
                            pass
                if max_page == 0:
                    return "Could not determine the last page. Please re-upload the document.", True
                page_num = max_page
            elif page_type == 'first':
                page_num = 1
            # else page_num already set from pattern
            
            if not page_num:
                return "", False
            
            # Method 1: Try to get from _document_pages (most reliable)
            try:
                if hasattr(processor, '_document_pages') and processor._document_pages:
                    pages_data = processor._document_pages.get(doc_id, [])
                    print(f"DEBUG: Looking in _document_pages for doc {doc_id}, found {len(pages_data)} pages")
                    if pages_data:
                        for pnum, ptext in pages_data:
                            if int(pnum) == int(page_num):
                                total_pages = len(pages_data)
                                print(f"DEBUG: Found page {page_num} in _document_pages, content length: {len(ptext)}")
                                return f"**Page {page_num} of {total_pages}:**\n\n{ptext.strip()}", True
            except Exception as e:
                print(f"Error getting from _document_pages: {e}")
                import traceback
                traceback.print_exc()
            
            # Method 2: Collect chunks from this page using metadata
            page_chunks = []
            for i, meta in enumerate(metadatas):
                if i >= len(documents):
                    break
                meta_page = meta.get('page_number')
                # Handle both int and string page numbers
                if isinstance(meta_page, str):
                    try:
                        meta_page = int(meta_page)
                    except:
                        try:
                            meta_page = int(float(meta_page))
                        except:
                            continue
                elif isinstance(meta_page, float):
                    meta_page = int(meta_page)
                
                if meta_page == page_num:
                    page_chunks.append(documents[i])
            
            if page_chunks:
                page_text = "\n\n".join(page_chunks).strip()
                if page_text:
                    # Calculate total pages
                    all_pages = []
                    for m in metadatas:
                        p = m.get('page_number')
                        if isinstance(p, (int, float)):
                            all_pages.append(int(p))
                        elif isinstance(p, str):
                            try:
                                all_pages.append(int(float(p)))
                            except:
                                pass
                    total_pages = max(all_pages + [1])
                    return f"**Page {page_num} of {total_pages}:**\n\n{page_text}", True
            
            return f"Page {page_num} content not found. The document may not have page information stored. Please re-upload the document.", True
            
        except Exception as e:
            print(f"Error in handle_page_query: {e}")
            import traceback
            traceback.print_exc()
            return "", False
    
    def select_best_chunks(self, query: str, search_results: List[Tuple[str, float]]) -> List[str]:
        """Select best chunks - prioritize chunks that contain the exact query term"""
        search_terms = self.extract_search_terms(query)
        if not search_terms:
            return [chunk for chunk, _ in search_results[:10]]
        
        primary_term = search_terms[0].lower()
        primary_words = set(primary_term.split())
        
        # Separate chunks: those with primary term vs others
        exact_matches = []
        other_chunks = []
        
        for chunk, distance in search_results:
            chunk_lower = chunk.lower()
            
            # Check if chunk contains primary term
            has_primary = False
            if len(primary_words) == 1:
                if re.search(rf'\b{re.escape(primary_term)}\b', chunk_lower):
                    has_primary = True
            else:
                if primary_term in chunk_lower or all(w in chunk_lower for w in primary_words):
                    has_primary = True
            
            if has_primary:
                # Score by definition pattern and distance
                score = 0
                if re.search(rf'\b{re.escape(primary_term)}\b\s+(?:is|means|defined|refers)', chunk_lower):
                    score += 20  # Big bonus for definition patterns
                score += max(0, 10 - (distance * 10))  # Distance bonus
                
                # Penalty for list chunks (mentions many other terms)
                other_terms = ['complete graph', 'bipartite', 'cycle', 'tree', 'path']
                other_count = sum(1 for term in other_terms 
                                if term in chunk_lower and term not in primary_words)
                if other_count >= 2:
                    score -= 5  # Slight penalty for lists
                
                exact_matches.append((score, chunk, distance))
            else:
                other_chunks.append((chunk, distance))
        
        # Sort exact matches by score
        exact_matches.sort(key=lambda x: x[0], reverse=True)
        
        # Return: top exact matches first, then top others
        result = []
        
        # Add top exact matches (up to 5)
        for score, chunk, distance in exact_matches[:5]:
            result.append(chunk)
        
        # If we need more, add from exact matches or top other chunks
        if len(result) < 5:
            for score, chunk, distance in exact_matches[5:]:
                result.append(chunk)
                if len(result) >= 10:
                    break
        
        if len(result) < 10:
            for chunk, distance in other_chunks:
                if chunk not in result:
                    result.append(chunk)
                if len(result) >= 10:
                    break
        
        return result if result else [chunk for chunk, _ in search_results[:10]]
    
    def query(self, user_query: str, n_results: int = 10) -> Tuple[str, List[str]]:
        """Process a user query using RAG"""
        # Check if we have documents
        has_docs = self.has_documents()
        
        if not has_docs:
            query_lower = user_query.lower()
            greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
            if any(g in query_lower for g in greetings) and len(user_query.split()) <= 3:
                return "Hello! 👋 Please upload a document (PDF, DOC, or DOCX) to ask questions about it.", []
            return "Please upload a document first. This chatbot answers questions based on your uploaded documents.", []
        
        # Handle greetings
        query_lower = user_query.lower()
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(g in query_lower for g in greetings) and len(user_query.split()) <= 3:
            return "Hello! I'm ready to answer questions about your uploaded documents. What would you like to know?", []
        
        # Handle page queries FIRST - before any other processing
        page_response, is_page_query = self.handle_page_query(query_lower)
        if is_page_query:
            # If page query was detected, MUST return page response (even if empty)
            # Don't fall through to normal search - page queries are explicit requests
            if page_response:
                return page_response, ["Uploaded Document"]
            else:
                # Page query detected but content not found - give helpful error
                return "I couldn't find the requested page. Please make sure the document has been uploaded recently (page information is only available for newly uploaded documents).", ["Uploaded Document"]
        
        # Search for relevant chunks
        try:
            # Search with original query
            search_results = self.document_processor.search_documents(user_query, n_results=30)
            
            # If no results, try with extracted terms
            if not search_results:
                search_terms = self.extract_search_terms(user_query)
                if search_terms:
                    # Try searching with just the main term
                    alt_query = search_terms[0]
                    search_results = self.document_processor.search_documents(alt_query, n_results=30)
            
            if not search_results:
                return "I couldn't find any relevant information about '{}' in the uploaded documents. Please check if the term exists in the document.".format(user_query), []
            
            # Select best chunks that match the query
            context_chunks = self.select_best_chunks(user_query, search_results)
            
            if not context_chunks:
                return "I couldn't find relevant information in the uploaded documents. Please try rephrasing your question.", []
            
            # Generate response
            response = self.generate_response(user_query, context_chunks, use_rag=True)
            
            return response, ["Uploaded Document"]
            
        except Exception as e:
            print(f"Error in RAGService.query: {e}")
            import traceback
            traceback.print_exc()
            return f"An error occurred: {str(e)}. Please try again.", []


# Global instance
rag_service = RAGService()

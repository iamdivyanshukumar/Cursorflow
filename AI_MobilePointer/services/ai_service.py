# services/ai_service.py
import openai
import os
import logging
from typing import Optional, Dict, List, Tuple
import json
import time
import numpy as np
from datetime import datetime
import hashlib
import pickle
import faiss  # Vector database for efficient similarity search

logger = logging.getLogger(__name__)

class VectorStore:
    """Simple vector store using FAISS for efficient similarity search"""
    
    def __init__(self, dimension: int = 1536):  # OpenAI embeddings dimension
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product index for cosine similarity
        self.metadata = []
        self.embeddings_cache = {}
        
    def add_embedding(self, embedding: np.ndarray, metadata: Dict):
        """Add embedding to the vector store"""
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        self.index.add(embedding)
        self.metadata.append(metadata)
        
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[float, Dict]]:
        """Search for similar embeddings"""
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append((float(score), self.metadata[idx]))
        return results
    
    def get_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get metadata by content hash"""
        for metadata in self.metadata:
            if metadata.get('content_hash') == content_hash:
                return metadata
        return None
    
    def save(self, filepath: str):
        """Save vector store to disk"""
        data = {
            'index': faiss.serialize_index(self.index),
            'metadata': self.metadata,
            'embeddings_cache': self.embeddings_cache
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str):
        """Load vector store from disk"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            self.index = faiss.deserialize_index(data['index'])
            self.metadata = data['metadata']
            self.embeddings_cache = data.get('embeddings_cache', {})

class ConversationManager:
    """Manage conversation history with vector-based context retrieval"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.conversation_history = {}
        
    def add_conversation(self, client_id: str, role: str, content: str, content_hash: str = None):
        """Add conversation turn with optional content reference"""
        if client_id not in self.conversation_history:
            self.conversation_history[client_id] = []
            
        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'content_hash': content_hash
        }
        self.conversation_history[client_id].append(turn)
        
        # Keep only last 20 messages
        if len(self.conversation_history[client_id]) > 20:
            self.conversation_history[client_id] = self.conversation_history[client_id][-20:]
    
    def get_relevant_context(self, client_id: str, query: str, max_turns: int = 6) -> List[Dict]:
        """Get relevant conversation context for the query"""
        if client_id not in self.conversation_history:
            return []
            
        # Return recent conversation turns
        return self.conversation_history[client_id][-max_turns:]
    
    def clear_history(self, client_id: str):
        """Clear conversation history for client"""
        if client_id in self.conversation_history:
            del self.conversation_history[client_id]

class AIService:
    def __init__(self, api_key: str = None, storage_path: str = "ai_storage"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("OpenAI API configured")
        else:
            logger.warning("OpenAI API key not provided")
        
        # Create storage directory
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize vector store and conversation manager
        self.vector_store = VectorStore()
        self.vector_store.load(os.path.join(storage_path, "vector_store.pkl"))
        
        self.conversation_manager = ConversationManager(self.vector_store)
        
        # Cache for OCR results to avoid repeated processing
        self.ocr_cache = {}
        self.cache_ttl = 3600  # 1 hour TTL
        
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key.startswith('sk-'))
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI"""
        if not self.is_configured():
            return None
            
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.vector_store.embeddings_cache:
            return self.vector_store.embeddings_cache[text_hash]
        
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # Cache the embedding
            self.vector_store.embeddings_cache[text_hash] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def _get_content_hash(self, text: str) -> str:
        """Generate hash for content to identify duplicates"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def store_content(self, text: str, metadata: Dict = None) -> str:
        """Store content in vector database and return content hash"""
        if not text:
            return None
            
        content_hash = self._get_content_hash(text)
        
        # Check if content already exists
        existing = self.vector_store.get_by_hash(content_hash)
        if existing:
            logger.info(f"Content already exists in vector store: {content_hash}")
            return content_hash
        
        # Generate embedding and store
        embedding = self._get_embedding(text)
        if embedding is not None:
            store_metadata = {
                'content_hash': content_hash,
                'content_preview': text[:200] + "..." if len(text) > 200 else text,
                'content_length': len(text),
                'timestamp': datetime.now().isoformat(),
                'type': 'ocr_content'
            }
            
            if metadata:
                store_metadata.update(metadata)
                
            self.vector_store.add_embedding(embedding, store_metadata)
            self.vector_store.save(os.path.join(self.storage_path, "vector_store.pkl"))
            logger.info(f"Stored content in vector store: {content_hash}")
        
        return content_hash
    
    def get_similar_content(self, query: str, threshold: float = 0.7, max_results: int = 3) -> List[Dict]:
        """Find similar content in vector store"""
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
            
        results = self.vector_store.search(query_embedding, k=max_results)
        return [metadata for score, metadata in results if score >= threshold]
    
    def cache_ocr_result(self, client_id: str, text: str, region: Dict = None) -> str:
        """Cache OCR result and return content hash"""
        cache_key = f"{client_id}_{hashlib.md5(json.dumps(region or {}).encode()).hexdigest()}"
        
        # Store in temporary cache
        self.ocr_cache[cache_key] = {
            'text': text,
            'timestamp': time.time(),
            'content_hash': self.store_content(text, {'client_id': client_id, 'region': region})
        }
        
        return self.ocr_cache[cache_key]['content_hash']
    
    def get_cached_ocr(self, client_id: str, region: Dict = None) -> Tuple[Optional[str], Optional[str]]:
        """Get cached OCR result - returns (text, content_hash)"""
        cache_key = f"{client_id}_{hashlib.md5(json.dumps(region or {}).encode()).hexdigest()}"
        
        cached = self.ocr_cache.get(cache_key)
        if cached and (time.time() - cached['timestamp']) < self.cache_ttl:
            logger.info(f"Using cached OCR result for client {client_id}")
            return cached['text'], cached['content_hash']
        
        return None, None
    
    def summarize_text(self, text: str, max_length: int = 500, client_id: str = "default") -> Optional[str]:
        """Summarize text using OpenAI with caching"""
        if not self.is_configured():
            return "❌ OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."
        
        if not text or len(text.strip()) < 10:
            return "❌ Not enough text to summarize. Please capture more content from the screen."
        
        try:
            # Store content in vector database
            content_hash = self.store_content(text, {
                'client_id': client_id,
                'operation': 'summarize'
            })
            
            prompt = f"""Please provide a concise summary of the following text in about {max_length} characters. Focus on the main points and key information:

{text[:3000]}  # Limit context length

Summary:"""
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides clear, concise summaries of text content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=30
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Store conversation
            self.conversation_manager.add_conversation(
                client_id, 
                "assistant", 
                f"Summary: {summary}",
                content_hash
            )
            
            return summary
            
        except openai.APITimeoutError:
            logger.error("OpenAI API timeout")
            return "⏰ Request timed out. Please try again."
        except openai.APIConnectionError:
            logger.error("OpenAI API connection error")
            return "🔌 Connection error. Please check your internet connection."
        except openai.RateLimitError:
            logger.error("OpenAI API rate limit")
            return "🚫 Rate limit exceeded. Please wait a moment and try again."
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"❌ Error generating summary: {str(e)}"
    
    def answer_question(self, text: str, question: str, client_id: str = "default") -> Optional[str]:
        """Answer question based on the provided text with context from vector store"""
        if not self.is_configured():
            return "❌ OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."
        
        if not text:
            return "❌ No text content available. Please capture screen content first."
        
        try:
            # Store current content
            current_content_hash = self.store_content(text, {
                'client_id': client_id,
                'operation': 'question_answer'
            })
            
            # Find similar historical content
            similar_content = self.get_similar_content(question)
            context_parts = []
            
            # Add current content as primary context
            context_parts.append(f"CURRENT CONTENT:\n{text[:2000]}")
            
            # Add relevant historical context
            for i, content_meta in enumerate(similar_content[:2]):  # Top 2 similar
                # We don't have the full content, but we can reference it
                context_parts.append(f"RELATED CONTENT {i+1}:\n{content_meta.get('content_preview', 'No preview available')}")
            
            full_context = "\n\n".join(context_parts)
            
            # Build conversation with context
            messages = [
                {"role": "system", "content": f"""You are a helpful assistant that answers questions based on the provided text content. 
                 Use only the information from the text below. If the answer cannot be found in the text, say so.
                 
                 Available Context:
                 {full_context}"""}
            ]
            
            # Add conversation history
            history = self.conversation_manager.get_relevant_context(client_id, question)
            messages.extend(history)
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                timeout=30
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_manager.add_conversation(client_id, "user", question)
            self.conversation_manager.add_conversation(
                client_id, 
                "assistant", 
                answer,
                current_content_hash
            )
            
            return answer
            
        except openai.APITimeoutError:
            logger.error("OpenAI API timeout")
            return "⏰ Request timed out. Please try again."
        except openai.APIConnectionError:
            logger.error("OpenAI API connection error")
            return "🔌 Connection error. Please check your internet connection."
        except openai.RateLimitError:
            logger.error("OpenAI API rate limit")
            return "🚫 Rate limit exceeded. Please wait a moment and try again."
        except Exception as e:
            logger.error(f"Question answering error: {e}")
            return f"❌ Error answering question: {str(e)}"
    
    def analyze_page_content(self, text: str, client_id: str = "default") -> Dict:
        """Analyze page content and provide insights with caching"""
        if not self.is_configured():
            return {"error": "OpenAI API key not configured"}
        
        if not text:
            return {"error": "No text content available"}
        
        try:
            # Store content
            content_hash = self.store_content(text, {
                'client_id': client_id,
                'operation': 'analyze'
            })
            
            prompt = f"""Analyze the following text content and provide:
1. Main topic/theme (one sentence)
2. Key points (3-5 bullet points)
3. Type of content (article, document, website, etc.)
4. Suggested questions to ask about this content

Text: {text[:2500]}

Please respond in this exact format:
Topic: [topic here]
Key Points: [bullet points here]
Content Type: [type here]
Suggested Questions: [questions here]"""
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes text content and provides structured insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.3,
                timeout=30
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse the structured response
            try:
                lines = analysis_text.split('\n')
                result = {}
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Topic:'):
                        result['topic'] = line.replace('Topic:', '').strip()
                    elif line.startswith('Key Points:'):
                        current_section = 'key_points'
                        result['key_points'] = []
                    elif line.startswith('Content Type:'):
                        result['content_type'] = line.replace('Content Type:', '').strip()
                        current_section = None
                    elif line.startswith('Suggested Questions:'):
                        current_section = 'suggested_questions'
                        result['suggested_questions'] = []
                    elif current_section and line.startswith('-'):
                        result[current_section].append(line[1:].strip())
                    elif current_section and line:
                        result[current_section].append(line)
                
                # Store conversation
                self.conversation_manager.add_conversation(
                    client_id,
                    "assistant",
                    f"Content Analysis: {result.get('topic', 'Unknown topic')}",
                    content_hash
                )
                
                return result
                
            except:
                # Fallback to text response
                return {"analysis": analysis_text}
                
        except openai.APITimeoutError:
            logger.error("OpenAI API timeout")
            return {"error": "Request timed out. Please try again."}
        except openai.APIConnectionError:
            logger.error("OpenAI API connection error")
            return {"error": "Connection error. Please check your internet connection."}
        except openai.RateLimitError:
            logger.error("OpenAI API rate limit")
            return {"error": "Rate limit exceeded. Please wait a moment and try again."}
        except Exception as e:
            logger.error(f"Content analysis error: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def clear_conversation_history(self, client_id: str = "default"):
        """Clear conversation history for a client"""
        self.conversation_manager.clear_history(client_id)
        logger.info(f"Cleared conversation history for client: {client_id}")
        
        # Also clear OCR cache for this client
        keys_to_remove = [k for k in self.ocr_cache.keys() if k.startswith(f"{client_id}_")]
        for key in keys_to_remove:
            del self.ocr_cache[key]
    
    def get_conversation_stats(self, client_id: str = "default") -> Dict:
        """Get statistics about stored content and conversations"""
        stats = {
            'total_content_items': len(self.vector_store.metadata),
            'conversation_turns': len(self.conversation_manager.conversation_history.get(client_id, [])),
            'ocr_cache_entries': len([k for k in self.ocr_cache.keys() if k.startswith(f"{client_id}_")]),
            'embeddings_cache_size': len(self.vector_store.embeddings_cache)
        }
        return stats
import anthropic
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from database.models import DocumentChunk, QueryLog
from config.config import Config
from config.cache import get_cache_manager
import json
import numpy as np
import logging
import os
import hashlib

logger = logging.getLogger(__name__)


class QueryEngine:
    def __init__(self, session):
        self.config = Config()
        self.session = session
        self.embedder = SentenceTransformer(self.config.EMBEDDING_MODEL)
        self.cache = get_cache_manager()

        # Initialize Anthropic client with error handling
        api_key = self.config.ANTHROPIC_API_KEY
        if not api_key or api_key == 'your-anthropic-api-key':
            logger.warning("Anthropic API key not set. AI responses will be limited.")
            self.client = None
        else:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.client = None

    def find_relevant_chunks(self, query, top_k=5):
        """Find the most relevant chunks for a query using vector similarity"""
        
        # Check cache first for search results
        cached_results = self.cache.get_search_results(query, top_k)
        if cached_results:
            logger.info("Retrieved search results from cache")
            # Reconstruct Result objects from cached data
            results = []
            for item in cached_results:
                class Result:
                    def __init__(self, data):
                        self.id = data['id']
                        self.chunk_text = data['chunk_text']
                        self.metadata = data['metadata']
                        self.similarity = data['similarity']
                results.append(Result(item))
            return results
        
        # Generate query embedding (check cache first)
        query_embedding = self.cache.get_query_embedding(query)
        if query_embedding:
            logger.info("Retrieved query embedding from cache")
        else:
            query_embedding = self.embedder.encode(query).tolist()
            self.cache.set_query_embedding(query, query_embedding)
            logger.info("Generated and cached query embedding")

        # Use native pgvector for efficient vector similarity search
        try:
            # Convert query embedding to numpy array for pgvector
            import numpy as np
            query_vector = np.array(query_embedding)
            
            # Use cosine distance operator (<->) for similarity search
            # Note: pgvector uses distance (lower is better), so we need to convert to similarity
            results = self.session.query(
                DocumentChunk,
                (1 - DocumentChunk.embedding.cosine_distance(query_vector)).label('similarity')
            ).filter(
                DocumentChunk.embedding.is_not(None)
            ).order_by(
                DocumentChunk.embedding.cosine_distance(query_vector)
            ).limit(
                self.config.VECTOR_SEARCH_LIMIT
            ).all()

            if not results:
                logger.warning("No document chunks found in database")
                return []

            # Filter by similarity threshold and take top_k
            filtered_results = []
            for chunk, similarity in results:
                if similarity >= self.config.SIMILARITY_THRESHOLD:
                    # Create a simple object that matches expected format
                    class Result:
                        def __init__(self, chunk, similarity):
                            self.id = chunk.id
                            self.chunk_text = chunk.chunk_text
                            self.metadata = chunk.meta_data
                            self.similarity = float(similarity)

                    filtered_results.append(Result(chunk, similarity))
                    
                    # Stop when we have enough results
                    if len(filtered_results) >= top_k:
                        break

            logger.info(f"Found {len(filtered_results)} relevant chunks using pgvector search")

            # Cache the search results
            self.cache.set_search_results(query, filtered_results, top_k)
            logger.info(f"Cached search results for query: {query[:50]}...")

            return filtered_results

        except Exception as e:
            logger.error(f"Error in pgvector search: {e}")
            logger.info("Falling back to basic search...")
            
            # Fallback to basic search without vector operations
            try:
                chunks = self.session.query(DocumentChunk).filter(
                    DocumentChunk.embedding.is_not(None)
                ).limit(100).all()
                
                if not chunks:
                    return []
                    
                # Simple text matching fallback
                results = []
                for chunk in chunks:
                    # Basic text similarity as fallback
                    query_lower = query.lower()
                    chunk_lower = chunk.chunk_text.lower()
                    
                    # Simple word overlap scoring
                    query_words = set(query_lower.split())
                    chunk_words = set(chunk_lower.split())
                    
                    if query_words and chunk_words:
                        overlap = len(query_words.intersection(chunk_words))
                        similarity = overlap / len(query_words.union(chunk_words))
                        
                        if similarity > 0.1:  # Basic threshold
                            class Result:
                                def __init__(self, chunk, similarity):
                                    self.id = chunk.id
                                    self.chunk_text = chunk.chunk_text
                                    self.metadata = chunk.meta_data
                                    self.similarity = float(similarity)
                            
                            results.append(Result(chunk, similarity))
                
                # Sort by similarity and take top_k
                results.sort(key=lambda x: x.similarity, reverse=True)
                return results[:top_k]
                
            except Exception as e2:
                logger.error(f"Fallback search also failed: {e2}")
                return []

    def generate_response(self, query, relevant_chunks):
        """Generate a response using Claude API or fallback method"""
        if not relevant_chunks:
            return "I couldn't find any relevant information in the documentation."

        # Prepare context from relevant chunks
        context_parts = []
        for chunk in relevant_chunks[:3]:  # Use top 3 chunks
            try:
                metadata = json.loads(chunk.meta_data) if chunk.meta_data else {}
                page_title = metadata.get('page_title', 'Unknown')
                context_parts.append(f"Source: {page_title}\n{chunk.chunk_text}")
            except:
                context_parts.append(chunk.chunk_text)

        context = "\n\n".join(context_parts)
        
        # Create a hash of the context for cache key
        context_hash = hashlib.md5(context.encode()).hexdigest()
        
        # Check cache first for AI response
        cached_response = self.cache.get_ai_response(query, context_hash)
        if cached_response:
            logger.info("Retrieved AI response from cache")
            return cached_response

        # If Anthropic client is available, use it
        if self.client:
            try:
                # Create prompt
                prompt = f"""You are an AI assistant helping with questions about business rules and projects based on Confluence documentation.

Context from relevant documentation:
{context}

User Question: {query}

Please provide a comprehensive answer based on the provided context. If the context doesn't contain enough information to answer the question fully, please indicate what information is missing."""

                # Generate response using Claude
                response = self.client.messages.create(
                    model=self.config.CLAUDE_MODEL,  # Use model from config
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                ai_response = response.content[0].text
                
                # Cache the AI response
                self.cache.set_ai_response(query, context_hash, ai_response)
                logger.info("Generated and cached AI response")
                
                return ai_response

            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                # Fall through to fallback method

        # Fallback: Simple response based on context
        logger.info("Using fallback response method (no AI)")
        response = f"Based on the documentation, here's what I found related to your question:\n\n"

        for i, chunk in enumerate(relevant_chunks[:3], 1):
            try:
                metadata = json.loads(chunk.meta_data) if chunk.meta_data else {}
                page_title = metadata.get('page_title', 'Unknown')
                response += f"{i}. From '{page_title}':\n{chunk.chunk_text[:200]}...\n\n"
            except:
                response += f"{i}. {chunk.chunk_text[:200]}...\n\n"

        response += f"\nSimilarity scores: {[f'{chunk.similarity:.2f}' for chunk in relevant_chunks[:3]]}"

        # Cache the fallback response too
        self.cache.set_ai_response(query, context_hash, response)
        logger.info("Generated and cached fallback response")
        
        return response

    def query(self, question):
        """Main query method"""
        logger.info(f"Processing query: {question}")

        # Find relevant chunks
        relevant_chunks = self.find_relevant_chunks(question)

        if not relevant_chunks:
            # Check if there are any chunks at all
            chunk_count = self.session.query(DocumentChunk).count()
            if chunk_count == 0:
                return "No documents have been indexed yet. Please run the sync and training scripts first."
            return "I couldn't find any relevant information in the documentation for your query."

        # Generate response
        response = self.generate_response(question, relevant_chunks)

        # Log query
        try:
            query_log = QueryLog(
                query=question,
                response=response,
                relevance_score=relevant_chunks[0].similarity if relevant_chunks else 0
            )
            self.session.add(query_log)
            self.session.commit()
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            self.session.rollback()

        return response
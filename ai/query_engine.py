import anthropic
from sentence_transformers import SentenceTransformer
from database.models import DocumentChunk, QueryLog
from config.config import Config
import json
import numpy as np
import logging

logger = logging.getLogger(__name__)


class QueryEngine:
    def __init__(self, session):
        config = Config()
        self.session = session
        self.embedder = SentenceTransformer(config.EMBEDDING_MODEL)

        # Initialize Anthropic client with error handling
        api_key = config.ANTHROPIC_API_KEY
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
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # For PostgreSQL without pgvector, we'll use a simpler approach
        # Get all chunks and calculate similarity in Python
        try:
            chunks = self.session.query(DocumentChunk).all()

            if not chunks:
                logger.warning("No document chunks found in database")
                return []

            # Calculate similarities
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    # Calculate cosine similarity
                    chunk_embedding = np.array(chunk.embedding)
                    query_embedding_np = np.array(query_embedding)

                    # Cosine similarity
                    similarity = np.dot(chunk_embedding, query_embedding_np) / (
                            np.linalg.norm(chunk_embedding) * np.linalg.norm(query_embedding_np)
                    )

                    similarities.append({
                        'chunk': chunk,
                        'similarity': float(similarity)
                    })

            # Sort by similarity and get top k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_chunks = similarities[:top_k]

            # Return in expected format
            results = []
            for item in top_chunks:
                chunk = item['chunk']

                # Create a simple object that matches expected format
                class Result:
                    def __init__(self, chunk, similarity):
                        self.id = chunk.id
                        self.chunk_text = chunk.chunk_text
                        self.metadata = chunk.metadata
                        self.similarity = similarity

                results.append(Result(chunk, item['similarity']))

            return results

        except Exception as e:
            logger.error(f"Error finding relevant chunks: {e}")
            return []

    def generate_response(self, query, relevant_chunks):
        """Generate a response using Claude API or fallback method"""
        if not relevant_chunks:
            return "I couldn't find any relevant information in the documentation."

        # Prepare context from relevant chunks
        context_parts = []
        for chunk in relevant_chunks[:3]:  # Use top 3 chunks
            try:
                metadata = json.loads(chunk.metadata) if chunk.metadata else {}
                page_title = metadata.get('page_title', 'Unknown')
                context_parts.append(f"Source: {page_title}\n{chunk.chunk_text}")
            except:
                context_parts.append(chunk.chunk_text)

        context = "\n\n".join(context_parts)

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
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                return response.content[0].text

            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                # Fall through to fallback method

        # Fallback: Simple response based on context
        logger.info("Using fallback response method (no AI)")
        response = f"Based on the documentation, here's what I found related to your question:\n\n"

        for i, chunk in enumerate(relevant_chunks[:3], 1):
            try:
                metadata = json.loads(chunk.metadata) if chunk.metadata else {}
                page_title = metadata.get('page_title', 'Unknown')
                response += f"{i}. From '{page_title}':\n{chunk.chunk_text[:200]}...\n\n"
            except:
                response += f"{i}. {chunk.chunk_text[:200]}...\n\n"

        response += f"\nSimilarity scores: {[f'{chunk.similarity:.2f}' for chunk in relevant_chunks[:3]]}"

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
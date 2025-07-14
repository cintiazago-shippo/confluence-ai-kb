import anthropic
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
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
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def find_relevant_chunks(self, query, top_k=5):
        """Find the most relevant chunks for a query using vector similarity"""
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Use PostgreSQL's vector similarity search
        # Note: This requires pgvector extension
        sql = text("""
                   SELECT id,
                          chunk_text,
                          metadata,
                          1 - (embedding <=> :query_embedding::vector) as similarity
                   FROM document_chunks
                   ORDER BY similarity DESC LIMIT :limit
                   """)

        results = self.session.execute(
            sql,
            {"query_embedding": query_embedding, "limit": top_k}
        ).fetchall()

        return results

    def generate_response(self, query, relevant_chunks):
        """Generate a response using Claude API"""
        # Prepare context from relevant chunks
        context = "\n\n".join([
            f"Source: {json.loads(chunk.metadata)['page_title']}\n{chunk.chunk_text}"
            for chunk in relevant_chunks
        ])

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

    def query(self, question):
        """Main query method"""
        logger.info(f"Processing query: {question}")

        # Find relevant chunks
        relevant_chunks = self.find_relevant_chunks(question)

        if not relevant_chunks:
            return "I couldn't find any relevant information in the documentation."

        # Generate response
        response = self.generate_response(question, relevant_chunks)

        # Log query
        query_log = QueryLog(
            query=question,
            response=response,
            relevance_score=relevant_chunks[0].similarity if relevant_chunks else 0
        )
        self.session.add(query_log)
        self.session.commit()

        return response
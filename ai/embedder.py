from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from database.models import DocumentChunk, ConfluencePage
from config.config import Config
import json
import logging

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    def __init__(self):
        config = Config()
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def create_chunks_and_embeddings(self, session):
        """Create chunks and embeddings for all documents"""
        pages = session.query(ConfluencePage).all()

        for page in pages:
            logger.info(f"Processing page: {page.title}")

            # Create chunks
            chunks = self.text_splitter.split_text(page.content)

            # Delete existing chunks for this page
            session.query(DocumentChunk).filter_by(page_id=page.id).delete()

            # Create new chunks with embeddings
            for idx, chunk_text in enumerate(chunks):
                # Generate embedding
                embedding = self.model.encode(chunk_text).tolist()

                # Create chunk record
                chunk = DocumentChunk(
                    page_id=page.id,
                    chunk_text=chunk_text,
                    chunk_index=idx,
                    embedding=embedding,
                    meta_data=json.dumps({
                        'page_title': page.title,
                        'space_key': page.space_key,
                        'url': page.url
                    })
                )
                session.add(chunk)

            session.commit()
            logger.info(f"Created {len(chunks)} chunks for page: {page.title}")
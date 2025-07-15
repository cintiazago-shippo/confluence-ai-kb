from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime

Base = declarative_base()


class ConfluencePage(Base):
    __tablename__ = 'confluence_pages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    space_key = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_modified = Column(DateTime)


class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(ARRAY(Float))  # For storing vector embeddings
    meta_data = Column(Text)  # JSON string for additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryLog(Base):
    __tablename__ = 'query_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    response = Column(Text)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
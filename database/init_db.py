from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config.config import Config

config = Config()

def init_database():
    """Initialize the database with required tables"""
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")
    return engine

def get_session():
    """Get a database session"""
    engine = create_engine(config.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
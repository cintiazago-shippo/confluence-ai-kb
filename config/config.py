import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Confluence
    CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
    CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME')
    CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
    CONFLUENCE_SPACE_KEY = os.getenv('CONFLUENCE_SPACE_KEY')

    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'confluence_kb')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # AI
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Claude model selection
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')

    # Embeddings
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Vector Search
    VECTOR_SEARCH_LIMIT = 100  # Maximum results to retrieve before filtering
    SIMILARITY_THRESHOLD = 0.5  # Minimum similarity score for results

    # Redis Cache
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
import sys
import os
from pathlib import Path

sys.path.append('..')

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.init_db import get_session
from ai.embedder import DocumentEmbedder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_model():
    """Create embeddings for all documents"""
    session = get_session()

    try:
        embedder = DocumentEmbedder()
        embedder.create_chunks_and_embeddings(session)
        logger.info("Model training (embedding creation) completed!")

    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    train_model()
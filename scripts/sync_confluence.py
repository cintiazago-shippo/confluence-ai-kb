import sys

sys.path.append('..')

from confluence.client import ConfluenceClient
from confluence.extractor import ContentExtractor
from database.init_db import get_session
from database.models import ConfluencePage
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_confluence_pages():
    """Sync Confluence pages to local PostgreSQL database"""
    client = ConfluenceClient()
    session = get_session()

    try:
        # Get all pages
        pages = client.get_all_pages()
        logger.info(f"Found {len(pages)} pages to sync")

        for page in pages:
            # Extract page data
            page_data = ContentExtractor.extract_page_data(page)

            # Check if page exists
            existing_page = session.query(ConfluencePage).filter_by(
                page_id=page_data['page_id']
            ).first()

            if existing_page:
                # Update existing page
                for key, value in page_data.items():
                    setattr(existing_page, key, value)
                logger.info(f"Updated page: {page_data['title']}")
            else:
                # Create new page
                new_page = ConfluencePage(**page_data)
                session.add(new_page)
                logger.info(f"Added new page: {page_data['title']}")

        session.commit()
        logger.info("Sync completed successfully!")

    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sync_confluence_pages()
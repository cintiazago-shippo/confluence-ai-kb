import sys
import os

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from confluence.client import ConfluenceClient
from confluence.extractor import ContentExtractor
from database.init_db import get_session, init_database
from database.models import ConfluencePage
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_confluence_pages():
    """Sync Confluence pages to local PostgreSQL database"""
    # Initialize database if needed
    init_database()

    client = ConfluenceClient()
    session = get_session()

    try:
        # Get all pages
        pages = client.get_all_pages()
        logger.info(f"Found {len(pages)} pages to sync")

        if not pages:
            logger.warning("No pages found. Check your Confluence settings:")
            logger.warning("- CONFLUENCE_URL: Is it correct?")
            logger.warning("- CONFLUENCE_SPACE_KEY: Does this space exist?")
            logger.warning("- CONFLUENCE_API_TOKEN: Is it valid?")
            return

        synced_count = 0
        updated_count = 0

        for page in pages:
            try:
                # Extract page data
                page_data = ContentExtractor.extract_page_data(page)

                # Skip if no content
                if not page_data.get('content'):
                    logger.warning(f"Skipping page with no content: {page_data.get('title', 'Unknown')}")
                    continue

                # Check if page exists
                existing_page = session.query(ConfluencePage).filter_by(
                    page_id=page_data['page_id']
                ).first()

                if existing_page:
                    # Update existing page
                    for key, value in page_data.items():
                        setattr(existing_page, key, value)
                    logger.info(f"Updated page: {page_data['title']}")
                    updated_count += 1
                else:
                    # Create new page
                    new_page = ConfluencePage(**page_data)
                    session.add(new_page)
                    logger.info(f"Added new page: {page_data['title']}")
                    synced_count += 1

            except Exception as e:
                logger.error(f"Error processing page {page.get('id', 'unknown')}: {str(e)}")
                continue

        session.commit()
        logger.info(f"Sync completed successfully!")
        logger.info(f"Added {synced_count} new pages, updated {updated_count} existing pages")

    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sync_confluence_pages()
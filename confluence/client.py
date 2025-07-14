from atlassian import Confluence
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self):
        config = Config()
        self.confluence = Confluence(
            url=config.CONFLUENCE_URL,
            username=config.CONFLUENCE_USERNAME,
            password=config.CONFLUENCE_API_TOKEN,
            cloud=True
        )
        self.space_key = config.CONFLUENCE_SPACE_KEY

    def get_all_pages(self, limit=None):
        """Get all pages from the configured space"""
        pages = []
        start = 0
        limit_per_request = 50

        while True:
            results = self.confluence.get_all_pages_from_space(
                self.space_key,
                start=start,
                limit=limit_per_request,
                expand='body.storage,version'
            )

            pages.extend(results)

            if len(results) < limit_per_request:
                break

            if limit and len(pages) >= limit:
                pages = pages[:limit]
                break

            start += limit_per_request

        logger.info(f"Retrieved {len(pages)} pages from Confluence")
        return pages

    def get_page_content(self, page_id):
        """Get the content of a specific page"""
        page = self.confluence.get_page_by_id(
            page_id,
            expand='body.storage,version'
        )
        return page
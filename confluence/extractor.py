from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


class ContentExtractor:
    @staticmethod
    def extract_text_from_html(html_content):
        """Extract clean text from Confluence HTML content"""
        if not html_content:
            return ""

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    @staticmethod
    def extract_page_data(page):
        """Extract relevant data from a Confluence page"""
        page_data = {
            'page_id': page['id'],
            'title': page['title'],
            'space_key': page['space']['key'] if 'space' in page else None,
            'url': page['_links']['webui'] if '_links' in page else None,
            'content': ContentExtractor.extract_text_from_html(
                page.get('body', {}).get('storage', {}).get('value', '')
            ),
            'last_modified': page.get('version', {}).get('when')
        }

        return page_data
#!/usr/bin/env python
"""
Test Confluence connection and configuration
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from config.config import Config
from atlassian import Confluence
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_confluence_connection():
    """Test the Confluence connection and configuration"""
    print("Testing Confluence Connection...")
    print("=" * 50)

    # Load configuration
    config = Config()

    # Display configuration (masked)
    print(f"Confluence URL: {config.CONFLUENCE_URL}")
    print(f"Username: {config.CONFLUENCE_USERNAME}")
    print(f"API Token: {'*' * 10 if config.CONFLUENCE_API_TOKEN else 'NOT SET'}")
    print(f"Space Key: {config.CONFLUENCE_SPACE_KEY}")
    print("=" * 50)

    # Check if credentials are set
    if not all([config.CONFLUENCE_URL, config.CONFLUENCE_USERNAME,
                config.CONFLUENCE_API_TOKEN, config.CONFLUENCE_SPACE_KEY]):
        print("\n❌ ERROR: Missing Confluence configuration!")
        print("Please update your .env file with:")
        print("- CONFLUENCE_URL")
        print("- CONFLUENCE_USERNAME")
        print("- CONFLUENCE_API_TOKEN")
        print("- CONFLUENCE_SPACE_KEY")
        return False

    try:
        # Create Confluence client
        print("\nConnecting to Confluence...")
        confluence = Confluence(
            url=config.CONFLUENCE_URL,
            username=config.CONFLUENCE_USERNAME,
            password=config.CONFLUENCE_API_TOKEN,
            cloud=True
        )

        # Test connection by getting space info
        print(f"\nTesting connection with space: {config.CONFLUENCE_SPACE_KEY}")
        space = confluence.get_space(config.CONFLUENCE_SPACE_KEY, expand='description.plain')

        if space:
            print(f"\n✅ SUCCESS: Connected to space '{space['name']}'")
            print(f"Space Key: {space['key']}")
            print(f"Space Type: {space['type']}")

            # Try to get page count
            pages = confluence.get_all_pages_from_space(
                config.CONFLUENCE_SPACE_KEY,
                start=0,
                limit=1
            )

            # Get total count
            total_pages = confluence.get_all_pages_from_space(
                config.CONFLUENCE_SPACE_KEY,
                start=0,
                limit=1,
                expand='metadata.labels'
            )

            print(f"\nSpace contains pages: {len(pages) > 0}")

            if len(pages) > 0:
                print(f"Sample page: '{pages[0]['title']}'")

            return True

    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to Confluence")
        print(f"Error details: {str(e)}")
        print("\nPossible causes:")
        print("1. Invalid API token")
        print("2. Incorrect Confluence URL")
        print("3. Space key doesn't exist")
        print("4. No permissions to access the space")
        print("\nTo create an API token:")
        print("1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens")
        print("2. Click 'Create API token'")
        print("3. Copy the token to your .env file")

        return False


if __name__ == "__main__":
    success = test_confluence_connection()
    sys.exit(0 if success else 1)
from database.init_db import get_session, init_database
from ai.query_engine import QueryEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Initialize database if needed
    init_database()

    # Create session
    session = get_session()

    # Create query engine
    query_engine = QueryEngine(session)

    print("Welcome to Confluence AI Knowledge Base!")
    print("Type 'quit' to exit\n")

    while True:
        question = input("Ask a question: ").strip()

        if question.lower() == 'quit':
            break

        if not question:
            continue

        try:
            response = query_engine.query(question)
            print(f"\nAnswer: {response}\n")
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            print("Sorry, I encountered an error processing your question.")

    session.close()
    print("Goodbye!")


if __name__ == "__main__":
    main()
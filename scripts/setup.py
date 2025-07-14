import subprocess
import sys
import os


def setup_project():
    """Setup the project environment"""
    print("Setting up Confluence AI Knowledge Base project...")

    # Install PostgreSQL pgvector extension
    print("\nNote: You need to install pgvector extension for PostgreSQL:")
    print("Run: CREATE EXTENSION vector; in your PostgreSQL database")

    # Create .env file from example
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                content = f.read()
            with open('.env', 'w') as f:
                f.write(content)
            print("\n.env file created. Please update it with your credentials.")

    # Initialize database
    from database.init_db import init_database
    init_database()
    print("\nDatabase initialized!")

    print("\nSetup complete! Next steps:")
    print("1. Update .env file with your credentials")
    print("2. Run: python scripts/sync_confluence.py")
    print("3. Run: python scripts/train_model.py")
    print("4. Run: python main.py")


if __name__ == "__main__":
    setup_project()
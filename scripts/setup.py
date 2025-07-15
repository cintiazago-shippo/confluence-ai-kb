#!/usr/bin/env python
"""
Setup Script - Initial project setup
"""

import subprocess
import sys
import os


def setup_project():
    """Setup the project environment"""
    print("Setting up Confluence AI Knowledge Base project...")

    # Add parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    # Install PostgreSQL pgvector extension
    print("\n" + "=" * 50)
    print("IMPORTANT: PostgreSQL Setup Required")
    print("=" * 50)
    print("You need to install pgvector extension for PostgreSQL:")
    print("\n1. Connect to PostgreSQL:")
    print("   psql -U postgres")
    print("\n2. Create database (if not exists):")
    print("   CREATE DATABASE confluence_kb;")
    print("\n3. Connect to the database:")
    print("   \\c confluence_kb")
    print("\n4. Install pgvector extension:")
    print("   CREATE EXTENSION vector;")
    print("=" * 50 + "\n")

    # Create .env file from example
    env_path = os.path.join(parent_dir, '.env')
    env_example_path = os.path.join(parent_dir, '.env.example')

    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            with open(env_example_path, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
            print("✓ .env file created. Please update it with your credentials.")
        else:
            print("✗ .env.example not found. Creating a template .env file...")
            env_template = """# Confluence Settings
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=YOUR_SPACE

# PostgreSQL Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=confluence_kb
DB_USER=postgres
DB_PASSWORD=your-password

# AI Settings
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key  # Optional, for embeddings
"""
            with open(env_path, 'w') as f:
                f.write(env_template)
            print("✓ .env file created with template. Please update it with your credentials.")
    else:
        print("✓ .env file already exists.")

    # Check if required directories exist
    directories = ['config', 'database', 'confluence', 'ai', 'scripts']
    for directory in directories:
        dir_path = os.path.join(parent_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✓ Created directory: {directory}/")

            # Create __init__.py files
            init_file = os.path.join(dir_path, '__init__.py')
            with open(init_file, 'w') as f:
                f.write("")

    # Try to initialize database
    print("\nAttempting to initialize database...")
    try:
        from database.init_db import init_database
        init_database()
        print("✓ Database initialized successfully!")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Make sure all Python files are in place.")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("  This might be because:")
        print("  1. PostgreSQL is not running")
        print("  2. Database credentials in .env are incorrect")
        print("  3. The database doesn't exist yet")
        print("  4. pgvector extension is not installed")
        print("\n  Please fix these issues and run the script again.")

    print("\n" + "=" * 50)
    print("Setup Status Summary")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Update .env file with your credentials:")
    print(f"   - Edit: {env_path}")
    print("\n2. Ensure PostgreSQL is set up with pgvector extension")
    print("\n3. Install Python dependencies:")
    print("   pip install -r requirements.txt")
    print("\n4. Sync Confluence data:")
    print("   python scripts/sync_confluence.py")
    print("\n5. Train the model:")
    print("   python scripts/train_model.py")
    print("\n6. Start querying:")
    print("   python main.py")
    print("=" * 50)


if __name__ == "__main__":
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    setup_project()
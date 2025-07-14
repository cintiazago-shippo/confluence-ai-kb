# Confluence AI Knowledge Base - Usage Guide

## Initial Setup

### 1. Clone the Project
```bash
# Clone the project
git clone <your-repo>
cd confluence-ai-kb
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 4. Setup PostgreSQL with pgvector
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE confluence_kb;

# Connect to the new database
\c confluence_kb

# Install pgvector extension
CREATE EXTENSION vector;

# Exit PostgreSQL
\q
```

### 5. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials
# You'll need to add:
# - Confluence URL and API token
# - PostgreSQL credentials
# - Anthropic API key
```

### 6. Run Initial Setup
```bash
# Initialize the database tables
python scripts/setup.py
```

## Running the System

### Step 1: Sync Confluence Data
```bash
# Import all Confluence pages from your space
python scripts/sync_confluence.py
```
This will:
- Connect to your Confluence instance
- Download all pages from the configured space
- Extract text content from HTML
- Store everything in PostgreSQL

### Step 2: Train the Model (Create Embeddings)
```bash
# Generate embeddings for all documents
python scripts/train_model.py
```
This will:
- Split documents into chunks
- Generate vector embeddings for each chunk
- Store embeddings in the database for fast retrieval

### Step 3: Query the System
```bash
# Start the interactive query interface
python main.py
```
This will:
- Start an interactive prompt
- Allow you to ask questions about your documentation
- Return AI-generated answers based on your Confluence content

## Example Prompting Patterns

### Business Rules Queries
```
What are the approval requirements for purchase orders over $10,000?
Explain the employee onboarding process
What are the data retention policies for customer information?
```

### Project Information
```
What is the timeline for Project Phoenix?
Who are the stakeholders for the mobile app redesign?
What are the success criteria for Q4 initiatives?
```

### Technical Documentation
```
How do I configure the payment gateway integration?
What are the API rate limits for external services?
Describe the deployment process for production releases
```

### Process and Procedures
```
What is the incident response procedure?
How do I request access to production systems?
What are the code review guidelines?
```

## Advanced Prompting Tips

### 1. Be Specific
Include project names, dates, or specific terms for better results:
```
What were the security requirements defined for Project Atlas in Q3 2024?
```

### 2. Ask for Comparisons
Compare different processes or policies:
```
What's the difference between standard and expedited procurement processes?
```

### 3. Request Summaries
Get concise overviews of complex topics:
```
Summarize the key points about our data security policies
```

### 4. Seek Relationships
Understand how different systems interact:
```
How does the billing system interact with inventory management?
```

### 5. Time-based Queries
Ask about changes or specific time periods:
```
What changed in the refund policy after January 2024?
```

## Troubleshooting

### Common Issues

#### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Verify connection details in .env file
# Ensure DB_HOST, DB_PORT, DB_USER, DB_PASSWORD are correct
```

#### Confluence API Error
```bash
# Verify your API token is valid
# Check CONFLUENCE_URL format (should include https://)
# Ensure CONFLUENCE_SPACE_KEY exists
```

#### Vector Extension Missing
```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

#### No Results Found
- Ensure sync_confluence.py ran successfully
- Check if pages exist in the database:
```sql
SELECT COUNT(*) FROM confluence_pages;
```

## Extending the System

### Add More Data Sources
Extend to include Jira, Slack, or other systems:
```python
# Create new extractors in similar pattern
# Add to sync process
```

### Improve Embeddings
Use OpenAI embeddings for better quality:
```python
# Update EMBEDDING_MODEL in config
# Modify embedder.py to use OpenAI API
```

### Add Caching
Implement Redis for faster repeated queries:
```python
# Add redis to requirements.txt
# Cache embeddings and frequent queries
```

### Create Web Interface
Build a user-friendly web interface:
```python
# Use Flask or FastAPI
# Add HTML templates for query interface
```

### Implement Feedback Loop
Allow users to rate responses:
```python
# Add rating field to query_logs table
# Use feedback to improve prompts
```

## Best Practices

1. **Regular Syncing**: Schedule regular Confluence syncs to keep data current
2. **Monitor Performance**: Track query response times and accuracy
3. **Backup Database**: Regular backups of your PostgreSQL database
4. **Security**: Keep API keys secure and use environment variables
5. **Documentation**: Keep your Confluence pages well-structured for better results

## Quick Command Reference

```bash
# Full setup and run sequence
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/setup.py
python scripts/sync_confluence.py
python scripts/train_model.py
python main.py

# Update data
python scripts/sync_confluence.py
python scripts/train_model.py

# Just query
python main.py
```
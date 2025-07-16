#!/usr/bin/env python3
"""
Database migration script to convert from ARRAY(Float) to vector(384) type
This script migrates existing embeddings to use pgvector format
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from database.init_db import get_session, init_database
from database.models import DocumentChunk
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_to_vector():
    """Migrate existing embeddings from ARRAY(Float) to vector(384) type"""
    
    logger.info("Starting migration to pgvector format...")
    
    # Get database connection
    config = Config()
    engine = create_engine(config.DATABASE_URL)
    session = get_session()
    
    try:
        # Step 1: Check if vector extension is available
        logger.info("Checking pgvector extension...")
        result = session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if not result.fetchone():
            logger.error("pgvector extension not found. Please install it first.")
            return False
        
        # Step 2: Check current schema
        logger.info("Checking current schema...")
        result = session.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding'
        """))
        
        column_info = result.fetchone()
        if not column_info:
            logger.error("embedding column not found in document_chunks table")
            return False
        
        logger.info(f"Current embedding column type: {column_info[1]} ({column_info[2]})")
        
        # Step 3: Check if we need to migrate
        if column_info[2] == 'vector':
            logger.info("Embedding column is already vector type. No migration needed.")
            return True
        
        # Step 4: Get count of existing records
        count_result = session.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
        record_count = count_result.scalar()
        logger.info(f"Found {record_count} records with embeddings to migrate")
        
        if record_count == 0:
            logger.info("No existing embeddings found. Proceeding with schema update only.")
        
        # Step 5: Create backup of existing data (optional but recommended)
        logger.info("Creating backup table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS document_chunks_backup AS 
            SELECT * FROM document_chunks WHERE embedding IS NOT NULL
        """))
        session.commit()
        
        # Step 6: Add new vector column
        logger.info("Adding new vector column...")
        try:
            session.execute(text("ALTER TABLE document_chunks ADD COLUMN embedding_vector vector(384)"))
            session.commit()
        except Exception as e:
            if "already exists" in str(e):
                logger.info("embedding_vector column already exists")
            else:
                raise
        
        # Step 7: Migrate existing data
        if record_count > 0:
            logger.info("Migrating existing embeddings...")
            
            # Get chunks with embeddings in batches
            batch_size = 100
            offset = 0
            
            while True:
                result = session.execute(text("""
                    SELECT id, embedding 
                    FROM document_chunks 
                    WHERE embedding IS NOT NULL 
                    LIMIT :limit OFFSET :offset
                """), {"limit": batch_size, "offset": offset})
                
                batch = result.fetchall()
                if not batch:
                    break
                
                # Convert each embedding
                for row in batch:
                    chunk_id, embedding_array = row
                    
                    if embedding_array and len(embedding_array) == 384:
                        # Convert array to vector format
                        vector_str = '[' + ','.join(map(str, embedding_array)) + ']'
                        
                        session.execute(text("""
                            UPDATE document_chunks 
                            SET embedding_vector = :vector 
                            WHERE id = :id
                        """), {"vector": vector_str, "id": chunk_id})
                    else:
                        logger.warning(f"Invalid embedding dimension for chunk {chunk_id}: {len(embedding_array) if embedding_array else 0}")
                
                session.commit()
                offset += batch_size
                logger.info(f"Migrated {min(offset, record_count)} / {record_count} records")
        
        # Step 8: Drop old column and rename new one
        logger.info("Updating schema...")
        session.execute(text("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding"))
        session.execute(text("ALTER TABLE document_chunks RENAME COLUMN embedding_vector TO embedding"))
        session.commit()
        
        # Step 9: Create indexes for performance
        logger.info("Creating vector indexes...")
        try:
            # Create HNSW index for cosine similarity
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_cosine 
                ON document_chunks USING hnsw (embedding vector_cosine_ops)
            """))
            
            # Create index for L2 distance
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_l2 
                ON document_chunks USING hnsw (embedding vector_l2_ops)
            """))
            
            session.commit()
            logger.info("Vector indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create HNSW indexes: {e}")
            logger.info("Falling back to IVFFlat index...")
            try:
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_ivfflat 
                    ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100)
                """))
                session.commit()
                logger.info("IVFFlat index created successfully")
            except Exception as e2:
                logger.warning(f"Could not create IVFFlat index: {e2}")
        
        # Step 10: Verify migration
        logger.info("Verifying migration...")
        result = session.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding'
        """))
        
        column_info = result.fetchone()
        if column_info and column_info[2] == 'vector':
            logger.info("✅ Migration completed successfully!")
            logger.info(f"New embedding column type: {column_info[1]} ({column_info[2]})")
            
            # Count migrated records
            count_result = session.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
            final_count = count_result.scalar()
            logger.info(f"✅ {final_count} embeddings migrated successfully")
            
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def cleanup_backup():
    """Remove backup table after successful migration"""
    session = get_session()
    try:
        session.execute(text("DROP TABLE IF EXISTS document_chunks_backup"))
        session.commit()
        logger.info("Backup table removed")
    except Exception as e:
        logger.error(f"Error removing backup table: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    success = migrate_to_vector()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use native pgvector search for improved performance.")
        
        # Ask if user wants to remove backup
        response = input("\nRemove backup table? (y/N): ").lower()
        if response == 'y':
            cleanup_backup()
    else:
        print("\n❌ Migration failed. Please check the logs and try again.")
        sys.exit(1)
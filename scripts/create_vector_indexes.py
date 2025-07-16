#!/usr/bin/env python3
"""
Script to create optimal vector indexes for pgvector performance
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.init_db import get_session
from database.models import DocumentChunk
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_vector_indexes():
    """Create optimized vector indexes for similarity search"""
    
    session = get_session()
    
    try:
        # Check if we have any vectors to index
        count_result = session.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
        vector_count = count_result.scalar()
        
        if vector_count == 0:
            logger.warning("No vectors found in database. Run sync and training first.")
            return False
            
        logger.info(f"Creating indexes for {vector_count} vectors...")
        
        # Drop existing indexes if they exist
        logger.info("Dropping existing vector indexes...")
        drop_commands = [
            "DROP INDEX IF EXISTS idx_document_chunks_embedding_cosine",
            "DROP INDEX IF EXISTS idx_document_chunks_embedding_l2", 
            "DROP INDEX IF EXISTS idx_document_chunks_embedding_ivfflat",
            "DROP INDEX IF EXISTS idx_document_chunks_embedding_hnsw"
        ]
        
        for cmd in drop_commands:
            try:
                session.execute(text(cmd))
            except Exception as e:
                logger.debug(f"Index drop failed (expected): {e}")
        
        session.commit()
        
        # Determine optimal index type based on vector count
        if vector_count < 1000:
            # For small datasets, use exact search (no index needed)
            logger.info("Small dataset detected. Using exact search (no index needed).")
            return True
        
        elif vector_count < 10000:
            # For medium datasets, use IVFFlat
            logger.info("Medium dataset detected. Creating IVFFlat index...")
            
            # Calculate optimal number of lists (rule of thumb: sqrt(rows))
            lists = max(10, min(100, int(vector_count ** 0.5)))
            
            session.execute(text(f"""
                CREATE INDEX idx_document_chunks_embedding_ivfflat 
                ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = {lists})
            """))
            
            logger.info(f"IVFFlat index created with {lists} lists")
            
        else:
            # For large datasets, prefer HNSW (if available)
            logger.info("Large dataset detected. Creating HNSW index...")
            
            try:
                # HNSW parameters
                # m: number of connections (higher = better recall, more memory)
                # ef_construction: search scope during construction (higher = better quality, slower build)
                m = 16  # Good balance for most use cases
                ef_construction = 64  # Good balance for most use cases
                
                session.execute(text(f"""
                    CREATE INDEX idx_document_chunks_embedding_hnsw 
                    ON document_chunks USING hnsw (embedding vector_cosine_ops) 
                    WITH (m = {m}, ef_construction = {ef_construction})
                """))
                
                logger.info(f"HNSW index created with m={m}, ef_construction={ef_construction}")
                
            except Exception as e:
                logger.warning(f"HNSW index creation failed: {e}")
                logger.info("Falling back to IVFFlat index...")
                
                # Fallback to IVFFlat
                lists = max(10, min(1000, int(vector_count ** 0.5)))
                
                session.execute(text(f"""
                    CREATE INDEX idx_document_chunks_embedding_ivfflat 
                    ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = {lists})
                """))
                
                logger.info(f"IVFFlat fallback index created with {lists} lists")
        
        session.commit()
        
        # Create additional indexes for other distance metrics if needed
        logger.info("Creating L2 distance index...")
        try:
            if vector_count >= 10000:
                # HNSW for L2 distance
                session.execute(text("""
                    CREATE INDEX idx_document_chunks_embedding_l2_hnsw 
                    ON document_chunks USING hnsw (embedding vector_l2_ops) 
                    WITH (m = 16, ef_construction = 64)
                """))
                logger.info("L2 HNSW index created")
            else:
                # IVFFlat for L2 distance
                lists = max(10, min(100, int(vector_count ** 0.5)))
                session.execute(text(f"""
                    CREATE INDEX idx_document_chunks_embedding_l2_ivfflat 
                    ON document_chunks USING ivfflat (embedding vector_l2_ops) 
                    WITH (lists = {lists})
                """))
                logger.info("L2 IVFFlat index created")
                
        except Exception as e:
            logger.warning(f"L2 index creation failed: {e}")
        
        session.commit()
        
        # Verify index creation
        logger.info("Verifying index creation...")
        result = session.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks' 
            AND indexname LIKE '%embedding%'
        """))
        
        indexes = result.fetchall()
        logger.info(f"Created {len(indexes)} vector indexes:")
        for idx_name, idx_def in indexes:
            logger.info(f"  - {idx_name}")
        
        # Test index performance
        logger.info("Testing index performance...")
        
        # Simple performance test
        test_vector = '[' + ','.join(['0.1'] * 384) + ']'
        
        import time
        start_time = time.time()
        
        result = session.execute(text("""
            SELECT id, embedding <=> :vector as distance 
            FROM document_chunks 
            WHERE embedding IS NOT NULL 
            ORDER BY embedding <=> :vector 
            LIMIT 10
        """), {"vector": test_vector})
        
        search_time = time.time() - start_time
        results = result.fetchall()
        
        logger.info(f"✅ Index performance test: {len(results)} results in {search_time:.3f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating vector indexes: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def analyze_index_usage():
    """Analyze index usage statistics"""
    session = get_session()
    
    try:
        logger.info("Analyzing index usage statistics...")
        
        # Get index usage stats
        result = session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE tablename = 'document_chunks' 
            AND indexname LIKE '%embedding%'
        """))
        
        stats = result.fetchall()
        
        if stats:
            logger.info("Index usage statistics:")
            for schema, table, idx_name, scans, tup_read, tup_fetch in stats:
                logger.info(f"  {idx_name}: {scans} scans, {tup_read} tuples read, {tup_fetch} tuples fetched")
        else:
            logger.info("No index usage statistics available yet")
            
    except Exception as e:
        logger.error(f"Error analyzing index usage: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    success = create_vector_indexes()
    
    if success:
        print("\n🎉 Vector indexes created successfully!")
        print("Your pgvector search performance should be significantly improved.")
        
        # Optionally show usage stats
        analyze_index_usage()
    else:
        print("\n❌ Index creation failed. Please check the logs.")
        sys.exit(1)
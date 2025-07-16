#!/usr/bin/env python3
"""
Test script for pgvector search functionality and performance
"""
import sys
import os
import time
# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.init_db import get_session
from database.models import DocumentChunk
from ai.query_engine import QueryEngine
from config.config import Config
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_vector_search_functionality():
    """Test vector search functionality"""
    print("Testing Vector Search Functionality...")
    
    session = get_session()
    config = Config()
    
    try:
        # Test 1: Check if vector extension is working
        print("1. Testing pgvector extension...")
        result = session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("   ✅ pgvector extension is installed")
        else:
            print("   ❌ pgvector extension not found")
            return False
        
        # Test 2: Check vector column type
        print("2. Checking vector column type...")
        result = session.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding'
        """))
        
        column_info = result.fetchone()
        if column_info and column_info[2] == 'vector':
            print(f"   ✅ embedding column is vector type: {column_info[2]}")
        else:
            print(f"   ❌ embedding column is not vector type: {column_info[2] if column_info else 'not found'}")
            return False
        
        # Test 3: Check for existing vectors
        print("3. Checking for existing vectors...")
        count_result = session.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
        vector_count = count_result.scalar()
        print(f"   Found {vector_count} vectors in database")
        
        if vector_count == 0:
            print("   ⚠️  No vectors found. Run sync and training first.")
            return False
        
        # Test 4: Check vector indexes
        print("4. Checking vector indexes...")
        result = session.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks' 
            AND indexname LIKE '%embedding%'
        """))
        
        indexes = result.fetchall()
        print(f"   Found {len(indexes)} vector indexes:")
        for idx_name, idx_def in indexes:
            print(f"     - {idx_name}")
        
        # Test 5: Test basic vector operations
        print("5. Testing basic vector operations...")
        
        # Get a sample vector
        result = session.execute(text("""
            SELECT embedding FROM document_chunks 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """))
        
        sample_vector = result.fetchone()
        if not sample_vector:
            print("   ❌ No sample vector found")
            return False
        
        # Test cosine distance
        test_vector = '[' + ','.join(['0.1'] * 384) + ']'
        
        result = session.execute(text("""
            SELECT id, embedding <=> :vector as distance 
            FROM document_chunks 
            WHERE embedding IS NOT NULL 
            ORDER BY embedding <=> :vector 
            LIMIT 5
        """), {"vector": test_vector})
        
        distances = result.fetchall()
        print(f"   ✅ Distance calculation successful: {len(distances)} results")
        
        # Test 6: Test QueryEngine integration
        print("6. Testing QueryEngine integration...")
        
        query_engine = QueryEngine(session)
        
        # Test search with a simple query
        start_time = time.time()
        results = query_engine.find_relevant_chunks("test query", top_k=5)
        search_time = time.time() - start_time
        
        print(f"   ✅ QueryEngine search: {len(results)} results in {search_time:.3f}s")
        
        if results:
            print(f"   Top result similarity: {results[0].similarity:.3f}")
        
        # Test 7: Performance comparison
        print("7. Running performance benchmark...")
        
        # Test with multiple queries
        test_queries = [
            "project timeline",
            "security requirements", 
            "deployment process",
            "api documentation",
            "user authentication"
        ]
        
        total_time = 0
        total_results = 0
        
        for query in test_queries:
            start_time = time.time()
            results = query_engine.find_relevant_chunks(query, top_k=10)
            query_time = time.time() - start_time
            
            total_time += query_time
            total_results += len(results)
            
            print(f"   Query '{query}': {len(results)} results in {query_time:.3f}s")
        
        avg_time = total_time / len(test_queries)
        print(f"   Average query time: {avg_time:.3f}s")
        print(f"   Total results: {total_results}")
        
        # Test 8: Test different similarity thresholds
        print("8. Testing similarity thresholds...")
        
        original_threshold = config.SIMILARITY_THRESHOLD
        
        for threshold in [0.1, 0.3, 0.5, 0.7]:
            config.SIMILARITY_THRESHOLD = threshold
            results = query_engine.find_relevant_chunks("test query", top_k=10)
            print(f"   Threshold {threshold}: {len(results)} results")
        
        # Restore original threshold
        config.SIMILARITY_THRESHOLD = original_threshold
        
        print("\n✅ All vector search tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Vector search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def benchmark_search_performance():
    """Benchmark search performance"""
    print("\nRunning Search Performance Benchmark...")
    
    session = get_session()
    
    try:
        # Check vector count
        count_result = session.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
        vector_count = count_result.scalar()
        
        print(f"Benchmarking against {vector_count} vectors...")
        
        if vector_count == 0:
            print("No vectors found for benchmarking")
            return
        
        query_engine = QueryEngine(session)
        
        # Test queries of different complexity
        test_queries = [
            "simple",
            "project management timeline",
            "authentication and authorization security requirements",
            "detailed technical documentation for API endpoints and integration",
            "comprehensive analysis of deployment procedures and best practices"
        ]
        
        results = []
        
        for query in test_queries:
            times = []
            result_counts = []
            
            # Run each query multiple times
            for _ in range(3):
                start_time = time.time()
                search_results = query_engine.find_relevant_chunks(query, top_k=10)
                query_time = time.time() - start_time
                
                times.append(query_time)
                result_counts.append(len(search_results))
            
            avg_time = sum(times) / len(times)
            avg_results = sum(result_counts) / len(result_counts)
            
            results.append({
                'query': query,
                'avg_time': avg_time,
                'avg_results': avg_results,
                'query_length': len(query.split())
            })
            
            print(f"Query: '{query[:30]}...'")
            print(f"  Average time: {avg_time:.3f}s")
            print(f"  Average results: {avg_results:.1f}")
            print(f"  Query length: {len(query.split())} words")
            print()
        
        # Performance analysis
        print("Performance Analysis:")
        print(f"  Total vectors: {vector_count}")
        print(f"  Fastest query: {min(r['avg_time'] for r in results):.3f}s")
        print(f"  Slowest query: {max(r['avg_time'] for r in results):.3f}s")
        print(f"  Average query time: {sum(r['avg_time'] for r in results) / len(results):.3f}s")
        
        # Performance expectations
        if vector_count < 1000:
            expected_time = 0.01  # 10ms for small datasets
        elif vector_count < 10000:
            expected_time = 0.05  # 50ms for medium datasets
        else:
            expected_time = 0.1   # 100ms for large datasets
        
        avg_time = sum(r['avg_time'] for r in results) / len(results)
        
        if avg_time <= expected_time:
            print(f"  ✅ Performance is excellent (< {expected_time}s expected)")
        elif avg_time <= expected_time * 2:
            print(f"  ⚠️  Performance is acceptable (< {expected_time*2}s)")
        else:
            print(f"  ❌ Performance needs improvement (> {expected_time*2}s)")
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    success = test_vector_search_functionality()
    
    if success:
        benchmark_search_performance()
        print("\n🎉 Vector search testing completed successfully!")
    else:
        print("\n❌ Vector search testing failed.")
        sys.exit(1)
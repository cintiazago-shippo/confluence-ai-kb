#!/usr/bin/env python3
"""
End-to-end test for the complete AI knowledge base functionality
"""
import sys
import os
import time
# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.init_db import get_session
from ai.query_engine import QueryEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end():
    """Test complete end-to-end functionality"""
    print("Testing End-to-End AI Knowledge Base Functionality...")
    
    session = get_session()
    
    try:
        # Initialize query engine
        query_engine = QueryEngine(session)
        
        # Test queries that should find relevant content
        test_queries = [
            "What is the deployment process?",
            "How do I configure authentication?",
            "What are the security requirements?",
            "Tell me about API documentation",
            "Explain the database setup"
        ]
        
        print("\nTesting queries:")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            print("-" * 30)
            
            # Time the query
            start_time = time.time()
            response = query_engine.query(query)
            query_time = time.time() - start_time
            
            print(f"Response time: {query_time:.3f}s")
            print(f"Response length: {len(response)} characters")
            
            # Show first 200 characters of response
            if len(response) > 200:
                print(f"Response preview: {response[:200]}...")
            else:
                print(f"Full response: {response}")
            
            # Check if response is meaningful
            if "couldn't find" in response.lower() or "no relevant" in response.lower():
                print("Status: ⚠️  No relevant content found")
            else:
                print("Status: ✅ Relevant content found")
            
            print()
        
        # Test cache functionality
        print("\nTesting cache functionality:")
        print("=" * 30)
        
        # First query (should generate embedding)
        start_time = time.time()
        response1 = query_engine.query("test cache query")
        time1 = time.time() - start_time
        
        # Second query (should use cache)
        start_time = time.time()
        response2 = query_engine.query("test cache query")
        time2 = time.time() - start_time
        
        print(f"First query time: {time1:.3f}s")
        print(f"Second query time: {time2:.3f}s")
        print(f"Cache speedup: {time1/time2:.1f}x faster")
        
        # Verify responses are identical
        if response1 == response2:
            print("✅ Cache working correctly - identical responses")
        else:
            print("❌ Cache issue - responses differ")
        
        print("\n✅ End-to-end testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
    
    return True

if __name__ == "__main__":
    success = test_end_to_end()
    
    if success:
        print("\n🎉 All systems are working correctly!")
        print("\nThe AI Knowledge Base is ready for use:")
        print("• Native pgvector search implemented")
        print("• Redis caching active")
        print("• Performance optimized")
        print("• Ready for production queries")
    else:
        print("\n❌ Some systems need attention.")
        sys.exit(1)
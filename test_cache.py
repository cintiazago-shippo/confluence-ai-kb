#!/usr/bin/env python3
"""
Simple test script to verify Redis caching functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.cache import get_cache_manager
import time

def test_cache_functionality():
    """Test basic cache operations"""
    print("Testing Redis Cache Functionality...")
    
    cache = get_cache_manager()
    
    # Test 1: Check if Redis is available
    print(f"1. Redis available: {cache.is_available()}")
    
    if not cache.is_available():
        print("   Warning: Redis not available, cache will be disabled in runtime")
        return
    
    # Test 2: Basic set/get operations
    test_key = "test_key"
    test_value = {"message": "Hello, Redis!", "timestamp": time.time()}
    
    print(f"2. Setting cache value: {test_value}")
    success = cache.set(test_key, test_value, ttl=60)
    print(f"   Set operation success: {success}")
    
    retrieved_value = cache.get(test_key)
    print(f"   Retrieved value: {retrieved_value}")
    print(f"   Values match: {retrieved_value == test_value}")
    
    # Test 3: Cache statistics
    stats = cache.get_stats()
    print(f"3. Cache stats: {stats}")
    
    # Test 4: Test specialized cache methods
    test_query = "What is the project timeline?"
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    print(f"4. Testing query embedding cache...")
    cache.set_query_embedding(test_query, test_embedding)
    cached_embedding = cache.get_query_embedding(test_query)
    print(f"   Embedding cached correctly: {cached_embedding == test_embedding}")
    
    # Test 5: Cache invalidation
    print(f"5. Testing cache invalidation...")
    cache.set("search:test1", {"data": "test1"})
    cache.set("search:test2", {"data": "test2"})
    cache.set("response:test1", {"data": "response1"})
    cache.set("other:test", {"data": "other"})
    
    deleted = cache.invalidate_content_cache()
    print(f"   Invalidated {deleted} entries")
    
    # Verify search and response caches are cleared
    print(f"   Search cache cleared: {cache.get('search:test1') is None}")
    print(f"   Response cache cleared: {cache.get('response:test1') is None}")
    print(f"   Other cache preserved: {cache.get('other:test') is not None}")
    
    # Test 6: Final statistics
    final_stats = cache.get_stats()
    print(f"6. Final cache stats: {final_stats}")
    
    print("\nCache functionality test completed!")

if __name__ == "__main__":
    test_cache_functionality()
import redis
import json
import logging
import hashlib
from typing import Any, Optional, Dict
from config.config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for the Confluence AI KB"""
    
    def __init__(self):
        self.config = Config()
        self.redis_client = None
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
        self._connect()
    
    def _connect(self):
        """Connect to Redis with error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                password=self.config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a consistent cache key"""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True)
        
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                self.cache_stats['hits'] += 1
                return json.loads(value)
            else:
                self.cache_stats['misses'] += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.config.CACHE_TTL
            serialized_value = json.dumps(value)
            success = self.redis_client.setex(key, ttl, serialized_value)
            if success:
                self.cache_stats['sets'] += 1
            return success
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            self.cache_stats['errors'] += 1
            return 0
    
    def get_query_embedding(self, query: str) -> Optional[list]:
        """Get cached query embedding"""
        key = self._generate_key("embedding", query)
        return self.get(key)
    
    def set_query_embedding(self, query: str, embedding: list) -> bool:
        """Cache query embedding"""
        key = self._generate_key("embedding", query)
        return self.set(key, embedding)
    
    def get_search_results(self, query: str, top_k: int = 5) -> Optional[list]:
        """Get cached search results"""
        search_key = {"query": query, "top_k": top_k}
        key = self._generate_key("search", search_key)
        return self.get(key)
    
    def set_search_results(self, query: str, results: list, top_k: int = 5) -> bool:
        """Cache search results"""
        search_key = {"query": query, "top_k": top_k}
        key = self._generate_key("search", search_key)
        # Serialize results to dict format for caching
        serializable_results = []
        for result in results:
            serializable_results.append({
                'id': str(result.id),
                'chunk_text': result.chunk_text,
                'metadata': result.metadata,
                'similarity': result.similarity
            })
        return self.set(key, serializable_results, ttl=1800)  # 30 minutes
    
    def get_ai_response(self, query: str, context_hash: str) -> Optional[str]:
        """Get cached AI response"""
        response_key = {"query": query, "context": context_hash}
        key = self._generate_key("response", response_key)
        return self.get(key)
    
    def set_ai_response(self, query: str, context_hash: str, response: str) -> bool:
        """Cache AI response"""
        response_key = {"query": query, "context": context_hash}
        key = self._generate_key("response", response_key)
        return self.set(key, response, ttl=7200)  # 2 hours
    
    def invalidate_content_cache(self):
        """Invalidate all content-related caches when content updates"""
        patterns = ["search:*", "response:*"]
        total_deleted = 0
        for pattern in patterns:
            deleted = self.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} cache entries due to content update")
        return total_deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.cache_stats.copy()
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['hits'] / total_requests
        else:
            stats['hit_rate'] = 0
        
        # Add Redis info if available
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_memory_used'] = info.get('used_memory_human', 'N/A')
                stats['redis_connected_clients'] = info.get('connected_clients', 0)
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
        
        return stats
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
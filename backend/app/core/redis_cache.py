import redis
import json
import logging
from functools import wraps
from typing import Optional, Callable, Any
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache client with automatic fallback to no-cache mode if Redis unavailable"""
    
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True):
        self.enabled = False
        self.client = None
        
        try:
            # Try to connect to Redis
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=decode_responses,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"✅ Redis connected successfully at {host}:{port}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️  Redis not available, caching disabled: {e}")
            self.client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value) if isinstance(value, str) else value
            return None
        except Exception as e:
            logger.error(f"Redis GET error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (time to live) in seconds"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis SET error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'user:*')"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis pattern delete error for {pattern}: {e}")
            return 0
    
    def cache_result(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator to cache function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"✨ Cache HIT: {cache_key}")
                    return cached_value
                
                # Cache miss - call the actual function
                logger.debug(f"💾 Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"✨ Cache HIT: {cache_key}")
                    return cached_value
                
                # Cache miss
                logger.debug(f"💾 Cache MISS: {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                return result
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Global Redis instance
redis_cache = RedisCache(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0))
)

# Convenience function for easy imports
def get_cache() -> RedisCache:
    """Get the global Redis cache instance"""
    return redis_cache

"""
Response Caching Middleware
Caches expensive API responses with TTL-based invalidation
"""
import time
import hashlib
import json
import logging
from functools import wraps
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

logger = logging.getLogger("ResponseCache")

# In-memory cache store
_cache = {}
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "invalidations": 0
}


class CacheEntry:
    """Represents a cached response with metadata"""
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.ttl = ttl_seconds
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def remaining_ttl(self) -> float:
        return max(0, self.expires_at - time.time())


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from prefix and arguments"""
    key_data = f"{prefix}:{json.dumps(args, sort_keys=True, default=str)}:{json.dumps(kwargs, sort_keys=True, default=str)}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cache_response(ttl_seconds: int = 60, key_prefix: str = None):
    """
    Decorator to cache function responses
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Optional prefix for cache key (defaults to function name)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Check cache
            if cache_key in _cache:
                entry = _cache[cache_key]
                if not entry.is_expired():
                    _cache_stats["hits"] += 1
                    logger.debug(f"Cache HIT: {prefix} (TTL: {entry.remaining_ttl():.1f}s)")
                    return entry.data
                else:
                    # Remove expired entry
                    del _cache[cache_key]
            
            _cache_stats["misses"] += 1
            logger.debug(f"Cache MISS: {prefix}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            _cache[cache_key] = CacheEntry(result, ttl_seconds)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Check cache
            if cache_key in _cache:
                entry = _cache[cache_key]
                if not entry.is_expired():
                    _cache_stats["hits"] += 1
                    logger.debug(f"Cache HIT: {prefix}")
                    return entry.data
                else:
                    del _cache[cache_key]
            
            _cache_stats["misses"] += 1
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = CacheEntry(result, ttl_seconds)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache(key_prefix: str = None, key: str = None):
    """Invalidate cache entries by prefix or specific key"""
    global _cache
    
    if key:
        if key in _cache:
            del _cache[key]
            _cache_stats["invalidations"] += 1
            logger.debug(f"Invalidated cache key: {key}")
    elif key_prefix:
        keys_to_delete = [k for k in _cache.keys() if k.startswith(key_prefix)]
        for k in keys_to_delete:
            del _cache[k]
            _cache_stats["invalidations"] += 1
        logger.debug(f"Invalidated {len(keys_to_delete)} cache entries with prefix: {key_prefix}")
    else:
        count = len(_cache)
        _cache = {}
        _cache_stats["invalidations"] += count
        logger.debug(f"Cleared entire cache ({count} entries)")


def get_cache_stats() -> dict:
    """Get cache statistics"""
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "entries": len(_cache),
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "hit_rate": f"{hit_rate:.1f}%",
        "invalidations": _cache_stats["invalidations"]
    }


def cleanup_expired():
    """Remove all expired cache entries"""
    global _cache
    expired_keys = [k for k, v in _cache.items() if v.is_expired()]
    for k in expired_keys:
        del _cache[k]
    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    return len(expired_keys)


# Pre-defined cache decorators for common use cases
def cache_market_data(func):
    """Cache market data for 30 seconds"""
    return cache_response(ttl_seconds=30, key_prefix="market")(func)

def cache_sentiment(func):
    """Cache sentiment data for 5 minutes"""
    return cache_response(ttl_seconds=300, key_prefix="sentiment")(func)

def cache_news(func):
    """Cache news for 5 minutes"""
    return cache_response(ttl_seconds=300, key_prefix="news")(func)

def cache_user_data(func):
    """Cache user data for 60 seconds"""
    return cache_response(ttl_seconds=60, key_prefix="user")(func)

from collections import defaultdict
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger("RateLimiter")

class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm with memory cleanup."""
    
    def __init__(self, cleanup_interval_seconds: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            cleanup_interval_seconds: How often to cleanup old user data (default: 1 hour)
        """
        self._requests = defaultdict(list)  # {user_id: [timestamp1, timestamp2, ...]}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval_seconds
        self._last_cleanup = datetime.now()
    
    def _cleanup_old_users(self):
        """Remove users who haven't made requests in the last cleanup interval."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self._cleanup_interval)
        
        users_to_remove = []
        for user_id, timestamps in self._requests.items():
            if not timestamps or (timestamps and timestamps[-1] < cutoff):
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self._requests[user_id]
        
        if users_to_remove:
            logger.info(f"Cleaned up {len(users_to_remove)} inactive users from rate limiter")
    
    def is_allowed(self, user_id: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Check if a request is allowed based on rate limit.
        
        Args:
            user_id: Unique identifier for the user
            limit: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds (default: 60)
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        with self._lock:
            # Periodic cleanup to prevent memory leak
            if (now - self._last_cleanup).total_seconds() > self._cleanup_interval:
                self._cleanup_old_users()
                self._last_cleanup = now
            
            # Remove old requests outside the window
            self._requests[user_id] = [
                ts for ts in self._requests[user_id] if ts > cutoff
            ]
            
            # Check if limit exceeded
            if len(self._requests[user_id]) >= limit:
                logger.warning(f"Rate limit exceeded for user {user_id}: {len(self._requests[user_id])}/{limit} requests")
                return False
            
            # Add current request
            self._requests[user_id].append(now)
            return True
    
    def reset(self, user_id: str):
        """Reset rate limit for a specific user."""
        with self._lock:
            if user_id in self._requests:
                del self._requests[user_id]
                logger.info(f"Rate limit reset for user {user_id}")
    
    def get_stats(self) -> dict:
        """Get statistics about the rate limiter."""
        with self._lock:
            return {
                "total_users": len(self._requests),
                "last_cleanup": self._last_cleanup.isoformat()
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

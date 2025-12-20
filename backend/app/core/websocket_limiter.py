"""
WebSocket Rate Limiter

Provides rate limiting for WebSocket connections.
Tracks connection attempts, concurrent connections, and message rates per user.
"""
import time
import asyncio
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger("WebSocketLimiter")


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    connection_id: str
    user_id: int
    connected_at: float
    message_timestamps: List[float] = field(default_factory=list)


class WebSocketRateLimiter:
    """
    Rate limiter for WebSocket connections.
    
    Tracks:
    - Connection attempts per user (prevents rapid reconnection)
    - Concurrent connections per user (prevents connection flooding)
    - Message rates per connection (prevents message spam)
    
    All tracking is in-memory with automatic cleanup.
    """
    
    def __init__(
        self,
        max_connections_per_user: int = 3,
        connection_rate_limit: int = 10,  # connections per hour
        message_rate_limit: int = 5,      # messages per minute
        rate_window: int = 60             # window in seconds
    ):
        """
        Initialize WebSocket rate limiter.
        
        Args:
            max_connections_per_user: Maximum concurrent connections per user
            connection_rate_limit: Maximum new connections per hour
            message_rate_limit: Maximum messages per minute per connection
            rate_window: Time window for rate limits in seconds
        """
        self.max_connections_per_user = max_connections_per_user
        self.connection_rate_limit = connection_rate_limit
        self.connection_rate_window = 3600  # 1 hour in seconds
        self.message_rate_limit = message_rate_limit
        self.message_rate_window = rate_window
        
        # Track active connections: {connection_id: ConnectionInfo}
        self.active_connections: Dict[str, ConnectionInfo] = {}
        
        # Track connection attempts: {user_id: [timestamps]}
        self.connection_attempts: Dict[int, List[float]] = defaultdict(list)
        
        # Cleanup task
        self._cleanup_task = None
        
        logger.info(
            f"WebSocket rate limiter initialized: "
            f"max_connections={max_connections_per_user}, "
            f"connection_rate={connection_rate_limit}/hour, "
            f"message_rate={message_rate_limit}/min"
        )
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background task to clean up old tracking data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
    
    async def _cleanup_old_data(self):
        """Remove old timestamps from tracking"""
        current_time = time.time()
        
        # Cleanup connection attempts older than 1 hour
        for user_id in list(self.connection_attempts.keys()):
            self.connection_attempts[user_id] = [
                ts for ts in self.connection_attempts[user_id]
                if current_time - ts < self.connection_rate_window
            ]
            if not self.connection_attempts[user_id]:
                del self.connection_attempts[user_id]
        
        # Cleanup message timestamps older than rate window
        for conn in self.active_connections.values():
            conn.message_timestamps = [
                ts for ts in conn.message_timestamps
                if current_time - ts < self.message_rate_window
            ]
    
    def _get_user_connections(self, user_id: int) -> List[ConnectionInfo]:
        """Get all active connections for a user"""
        return [
            conn for conn in self.active_connections.values()
            if conn.user_id == user_id
        ]
    
    async def check_connection_allowed(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if user can establish a new connection.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        current_time = time.time()
        
        # Check concurrent connection limit
        current_connections = self._get_user_connections(user_id)
        if len(current_connections) >= self.max_connections_per_user:
            return False, (
                f"Maximum concurrent connections ({self.max_connections_per_user}) reached. "
                f"Please close an existing connection first."
            )
        
        # Check connection rate limit (recent attempts)
        recent_attempts = [
            ts for ts in self.connection_attempts[user_id]
            if current_time - ts < self.connection_rate_window
        ]
        
        if len(recent_attempts) >= self.connection_rate_limit:
            oldest_attempt = min(recent_attempts)
            wait_time = int(self.connection_rate_window - (current_time - oldest_attempt))
            return False, (
                f"Connection rate limit exceeded ({self.connection_rate_limit}/hour). "
                f"Please wait {wait_time} seconds before reconnecting."
            )
        
        return True, "Connection allowed"
    
    async def track_connection(self, user_id: int, connection_id: str):
        """
        Register a new connection.
        
        Args:
            user_id: User ID
            connection_id: Unique connection identifier
        """
        current_time = time.time()
        
        # Record connection attempt
        self.connection_attempts[user_id].append(current_time)
        
        # Track active connection
        self.active_connections[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            connected_at=current_time
        )
        
        logger.info(f"User {user_id} connected (ID: {connection_id}). Total connections: {len(self._get_user_connections(user_id))}")
    
    async def remove_connection(self, user_id: int, connection_id: str):
        """
        Remove a connection when closed.
        
        Args:
            user_id: User ID
            connection_id: Connection identifier
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"User {user_id} disconnected (ID: {connection_id}). Remaining connections: {len(self._get_user_connections(user_id))}")
    
    async def check_message_allowed(self, user_id: int, connection_id: str) -> Tuple[bool, str]:
        """
        Check if user can send another message.
        
        Args:
            user_id: User ID
            connection_id: Connection identifier
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if connection_id not in self.active_connections:
            return False, "Connection not found"
        
        conn = self.active_connections[connection_id]
        current_time = time.time()
        
        # Count recent messages within the rate window
        recent_messages = [
            ts for ts in conn.message_timestamps
            if current_time - ts < self.message_rate_window
        ]
        
        if len(recent_messages) >= self.message_rate_limit:
            oldest_message = min(recent_messages)
            wait_time = int(self.message_rate_window - (current_time - oldest_message))
            return False, (
                f"Message rate limit exceeded ({self.message_rate_limit}/{self.message_rate_window}s). "
                f"Please wait {wait_time} seconds before sending another request."
            )
        
        return True, "Message allowed"
    
    async def track_message(self, user_id: int, connection_id: str):
        """
        Record a message from user.
        
        Args:
            user_id: User ID
            connection_id: Connection identifier
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to track message for unknown connection: {connection_id}")
            return
        
        conn = self.active_connections[connection_id]
        conn.message_timestamps.append(time.time())
        
        logger.debug(f"Message tracked for user {user_id} (connection {connection_id}). Total recent messages: {len(conn.message_timestamps)}")
    
    def get_stats(self) -> Dict:
        """Get current rate limiter statistics"""
        return {
            "total_active_connections": len(self.active_connections),
            "users_with_connections": len(set(conn.user_id for conn in self.active_connections.values())),
            "total_users_tracked": len(self.connection_attempts)
        }


# Global singleton instance
ws_limiter = WebSocketRateLimiter(
    max_connections_per_user=3,
    connection_rate_limit=10,  # 10 connections per hour
    message_rate_limit=5,      # 5 messages per minute
    rate_window=60
)

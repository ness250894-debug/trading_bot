"""
Tests for WebSocket Rate Limiter

Tests connection and message rate limiting functionality.
"""
import pytest
import asyncio
import time
from backend.app.core.websocket_limiter import WebSocketRateLimiter


@pytest.mark.asyncio
async def test_connection_limit():
    """Test max concurrent connections per user"""
    limiter = WebSocketRateLimiter(max_connections_per_user=2)
    
    # Allow first 2 connections
    allowed, _ = await limiter.check_connection_allowed(user_id=1)
    assert allowed
    await limiter.track_connection(1, "conn1")
    
    allowed, _ = await limiter.check_connection_allowed(user_id=1)
    assert allowed
    await limiter.track_connection(1, "conn2")
    
    # Block 3rd connection
    allowed, reason = await limiter.check_connection_allowed(user_id=1)
    assert not allowed
    assert "concurrent" in reason.lower()
    
    # Different user should be allowed
    allowed, _ = await limiter.check_connection_allowed(user_id=2)
    assert allowed


@pytest.mark.asyncio
async def test_connection_cleanup():
    """Test connection removal"""
    limiter = WebSocketRateLimiter(max_connections_per_user=2)
    
    await limiter.track_connection(1, "conn1")
    await limiter.track_connection(1, "conn2")
    
    # Should be at limit
    allowed, _ = await limiter.check_connection_allowed(user_id=1)
    assert not allowed
    
    # Remove one connection
    await limiter.remove_connection(1, "conn1")
    
    # Should now allow new connection
    allowed, _ = await limiter.check_connection_allowed(user_id=1)
    assert allowed


@pytest.mark.asyncio
async def test_message_rate_limit():
    """Test message rate limiting"""
    limiter = WebSocketRateLimiter(message_rate_limit=3, rate_window=60)
    
    await limiter.track_connection(1, "conn1")
    
    # Allow first 3 messages
    for i in range(3):
        allowed, _ = await limiter.check_message_allowed(1, "conn1")
        assert allowed
        await limiter.track_message(1, "conn1")
    
    # Block 4th message
    allowed, reason = await limiter.check_message_allowed(1, "conn1")
    assert not allowed
    assert "rate limit" in reason.lower()


@pytest.mark.asyncio
async def test_message_rate_window():
    """Test that message rate limit window works"""
    limiter = WebSocketRateLimiter(message_rate_limit=2, rate_window=1)  # 1 second window
    
    await limiter.track_connection(1, "conn1")
    
    # Send 2 messages
    await limiter.track_message(1, "conn1")
    await limiter.track_message(1, "conn1")
    
    # Should be blocked
    allowed, _ = await limiter.check_message_allowed(1, "conn1")
    assert not allowed
    
    # Wait for window to pass
    await asyncio.sleep(1.1)
    
    # Should be allowed now
    allowed, _ = await limiter.check_message_allowed(1, "conn1")
    assert allowed


@pytest.mark.asyncio
async def test_connection_rate_limit():
    """Test connection rate limiting"""
    limiter = WebSocketRateLimiter(
        max_connections_per_user=10,  # High limit to avoid concurrent limit
        connection_rate_limit=3,       # Only 3 connections per hour
        connection_rate_window=3600
    )
    
    # First 3 connections should be allowed
    for i in range(3):
        allowed, _ = await limiter.check_connection_allowed(user_id=1)
        assert allowed
        await limiter.track_connection(1, f"conn{i}")
        # Remove immediately to avoid concurrent limit
        await limiter.remove_connection(1, f"conn{i}")
    
    # 4th connection should be blocked by rate limit
    allowed, reason = await limiter.check_connection_allowed(user_id=1)
    assert not allowed
    assert "rate limit" in reason.lower()


@pytest.mark.asyncio
async def test_multiple_users_independent():
    """Test that rate limits are per-user"""
    limiter = WebSocketRateLimiter(message_rate_limit=2, rate_window=60)
    
    # User 1
    await limiter.track_connection(1, "conn1_user1")
    await limiter.track_message(1, "conn1_user1")
    await limiter.track_message(1, "conn1_user1")
    
    # User 1 should be rate limited
    allowed, _ = await limiter.check_message_allowed(1, "conn1_user1")
    assert not allowed
    
    # User 2 should not be affected
    await limiter.track_connection(2, "conn1_user2")
    allowed, _ = await limiter.check_message_allowed(2, "conn1_user2")
    assert allowed


@pytest.mark.asyncio
async def test_stats():
    """Test statistics retrieval"""
    limiter = WebSocketRateLimiter()
    
    await limiter.track_connection(1, "conn1")
    await limiter.track_connection(2, "conn2")
    
    stats = limiter.get_stats()
    
    assert stats['total_active_connections'] == 2
    assert stats['users_with_connections'] == 2


@pytest.mark.asyncio
async def test_cleanup_old_data():
    """Test that old timestamps are cleaned up"""
    limiter = WebSocketRateLimiter(message_rate_limit=5, rate_window=1)
    
    await limiter.track_connection(1, "conn1")
    
    # Add some messages
    for _ in range(3):
        await limiter.track_message(1, "conn1")
    
    # Wait for cleanup window
    await asyncio.sleep(1.1)
    
    # Trigger cleanup
    await limiter._cleanup_old_data()
    
    # Messages should have been cleaned up, so we should be able to send more
    allowed, _ = await limiter.check_message_allowed(1, "conn1")
    assert allowed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

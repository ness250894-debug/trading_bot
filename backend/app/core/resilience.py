"""
Resilience utilities for the trading bot.
Includes retry logic and circuit breaker patterns.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple

logger = logging.getLogger("Resilience")


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: Tuple = (Exception,)):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each attempt (exponential backoff)
        exceptions: Tuple of exceptions to catch and retry on
    
    Example:
        @retry(max_attempts=3, delay=1, backoff=2)
        def fetch_data():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}")
                    logger.info(f"Retrying in {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # Should never reach here, but for safety
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    
    When errors exceed threshold in a time window, the circuit "opens"
    and prevents further attempts for a cooldown period.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Circuit broken, all calls fail immediately
    - HALF_OPEN: Testing if service recovered
    
    Example:
        breaker = CircuitBreaker(threshold=5, window=60, cooldown=300)
        
        if breaker.is_open():
            logger.warning("Circuit breaker is open, skipping operation")
            return None
            
        try:
            result = risky_operation()
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise
    """
    
    def __init__(self, threshold: int = 5, window: int = 60, cooldown: int = 300):
        """
        Args:
            threshold: Number of failures before opening circuit
            window: Time window in seconds to count failures
            cooldown: Cooldown period in seconds before attempting recovery
        """
        self.threshold = threshold
        self.window = window
        self.cooldown = cooldown
        
        self.failure_times = []
        self.opened_at: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_failure(self):
        """Record a failure event."""
        current_time = time.time()
        self.failure_times.append(current_time)
        
        # Remove failures outside the time window
        cutoff = current_time - self.window
        self.failure_times = [t for t in self.failure_times if t > cutoff]
        
        # Check if threshold exceeded
        if len(self.failure_times) >= self.threshold and self.state == "CLOSED":
            self.state = "OPEN"
            self.opened_at = current_time
            logger.warning(f"🔴 Circuit breaker OPENED: {len(self.failure_times)} failures in {self.window}s")
    
    def record_success(self):
        """Record a successful operation."""
        if self.state == "HALF_OPEN":
            # Success in half-open state, close the circuit
            self.state = "CLOSED"
            self.failure_times = []
            self.opened_at = None
            logger.info("🟢 Circuit breaker CLOSED: Service recovered")
        elif self.state == "CLOSED":
            # Clear old failures on success
            self.failure_times = []
    
    def is_open(self) -> bool:
        """Check if circuit is currently open."""
        if self.state == "CLOSED":
            return False
        
        if self.state == "OPEN":
            # Check if cooldown period passed
            if self.opened_at and (time.time() - self.opened_at) >= self.cooldown:
                self.state = "HALF_OPEN"
                logger.info("🟡 Circuit breaker HALF-OPEN: Testing recovery")
                return False
            return True
        
        # HALF_OPEN state - allow one attempt
        return False
    
    def get_state(self) -> str:
        """Get current state for logging."""
        return self.state
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds."""
        if self.state != "OPEN" or not self.opened_at:
            return 0.0
        
        elapsed = time.time() - self.opened_at
        remaining = max(0, self.cooldown - elapsed)
        return remaining

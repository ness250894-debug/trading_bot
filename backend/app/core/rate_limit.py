"""Rate limiting configuration for the API."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("RateLimit")

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300/minute"],  # Global default
    storage_uri="memory://",  # Use in-memory storage (consider Redis for production)
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    """
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": 429,
                "message": "Rate limit exceeded. Please try again later.",
                "detail": str(exc.detail)
            }
        },
        headers={"Retry-After": str(exc.detail.split()[-1])}
    )

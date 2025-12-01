"""
HTTPS Enforcement Middleware for Production.

Automatically redirects HTTP requests to HTTPS and adds security headers.
Only active when ENVIRONMENT=production.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import os
import logging

logger = logging.getLogger("HTTPSMiddleware")


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Redirect HTTP to HTTPS in production and add security headers.
    
    Features:
    - Automatic HTTP → HTTPS redirect (301 permanent)
    - HSTS (HTTP Strict Transport Security) header
    - Additional security headers (X-Frame-Options, etc.)
    - Only active in production environment
    """
    
    async def dispatch(self, request, call_next):
        environment = os.getenv("ENVIRONMENT", "development")
        
        # Only enforce HTTPS redirect in production
        if environment == "production":
            # Check if request is HTTP (not HTTPS)
            if request.url.scheme == "http":
                # Build HTTPS URL
                https_url = request.url.replace(scheme="https")
                logger.info(f"Redirecting HTTP → HTTPS: {request.url} → {https_url}")
                return RedirectResponse(https_url, status_code=301)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers in production
        if environment == "production":
            # HSTS: Force HTTPS for 1 year, including subdomains
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # XSS Protection (legacy, but doesn't hurt)
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

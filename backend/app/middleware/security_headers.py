from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to every response.
    Encourages HTTPS, prevents clickjacking, and enforces content type security.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HTTP Strict Transport Security (HSTS)
        # Tells browsers to only access this site via HTTPS for the next year (31536000 seconds)
        # includeSubDomains applies this to all subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Frame-Options
        # DENY prevents the page from being rendered in a <frame>, <iframe> or <object>
        # effectively preventing clickjacking attacks.
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        # nosniff prevents the browser from trying to guess the MIME type, 
        # protecting against MIME sniffing vulnerabilities.
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer-Policy
        # Controls how much referrer information (the URL the user is coming from) is included with requests.
        # 'strict-origin-when-cross-origin' sends full URL for same-origin, only domain for cross-origin.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy (CSP)
        # A basic policy to prevent XSS. 
        # This might need fine-tuning depending on external scripts loaded by the frontend.
        # For now, we allow scripts from self and inline scripts (common in React apps unfortunately), 
        # but restrict object-src.
        # Note: Vite dev server often needs unsafe-inline/eval. 
        # We set a stricter policy but allow unsafe-inline for compatibility.
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' ws: wss: https:;"

        return response

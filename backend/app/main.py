from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import threading
from .core import bot as trading_bot
from .core.logging_utils import manager, AsyncWebSocketLogHandler
from .api import backtest, bot, trades, auth, api_keys, health, user, billing, exchanges
from .core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configure logging
# We need to get the root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

app = FastAPI(title="Trading Bot API", version="1.0.0")

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS configuration - strict validation for production
import os

# Check if running in production
environment = os.getenv("ENVIRONMENT", "development")
allowed_origins_str = os.getenv("CORS_ORIGINS", "")

# Validate and configure CORS
if not allowed_origins_str or allowed_origins_str.strip() == "":
    if environment == "production":
        raise ValueError("🚨 CORS_ORIGINS must be explicitly configured in production. Set ENVIRONMENT=development for dev mode.")
    else:
        logger.warning("⚠️ CORS not configured, defaulting to localhost")
        allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    
    # Prevent wildcard in production
    if "*" in allowed_origins:
        if environment == "production":
            raise ValueError("🚨 CORS_ORIGINS cannot be '*' in production. Specify allowed domains explicitly.")
        else:
            logger.warning("⚠️ CORS is set to allow all origins. This is INSECURE for production!")

logger.info(f"CORS allowed origins: {allowed_origins}")

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# API Routers
app.include_router(backtest.router, prefix="/api")
app.include_router(bot.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(exchanges.router, prefix="/api")

# Admin Router
from .api import admin
app.include_router(admin.router, prefix="/api")

# Visual Strategy Builder
from .api import visual_strategies
app.include_router(visual_strategies.router, prefix="/api")

# AI-Powered Insights
from .api import sentiment
app.include_router(sentiment.router, prefix="/api")

# Social Trading / Marketplace
from .api import marketplace
app.include_router(marketplace.router, prefix="/api")

# Serve Static Files (Frontend)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if dist folder exists (Production)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If API path, let it pass through (handled by routers above)
        # Also exclude assets and favicon to prevent returning index.html for them
        if full_path.startswith("api") or full_path.startswith("ws") or full_path.startswith("assets"):
            return {"status": 404, "message": "Not Found"}
        
        # Serve favicon if requested
        if full_path == "favicon.ico" or full_path == "vite.svg":
             if os.path.exists(os.path.join(frontend_dist, full_path)):
                 return FileResponse(os.path.join(frontend_dist, full_path))
             return {"status": 404, "message": "Not Found"}
            
        # Serve index.html for any other path (SPA)
        if os.path.exists(os.path.join(frontend_dist, "index.html")):
             return FileResponse(os.path.join(frontend_dist, "index.html"))
        return {"status": 404, "message": "Frontend not found"}

    @app.get("/")
    async def serve_root():
        if os.path.exists(os.path.join(frontend_dist, "index.html")):
            return FileResponse(os.path.join(frontend_dist, "index.html"))
        return {"status": 404, "message": "Frontend not found"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Trading Bot API is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    
    # 1. Setup WebSocket Logging
    loop = asyncio.get_running_loop()
    ws_handler = AsyncWebSocketLogHandler(manager, loop)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ws_handler.setFormatter(formatter)
    
    # Attach to Root Logger so we catch everything (including Bot)
    root_logger = logging.getLogger()
    root_logger.addHandler(ws_handler)
    
    # 2. Bot no longer starts automatically
    # Users must explicitly start their bot via /api/start endpoint
    logger.info("✓ Server ready. Bots can be started via API endpoints.")
    logger.info("ℹ️ Bot auto-start is disabled. Use /api/start to begin trading.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import threading
from .api import backtest, bot
from .core import bot as trading_bot
from .core.logging_utils import manager, AsyncWebSocketLogHandler

# Configure logging
# We need to get the root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

app = FastAPI(title="Trading Bot API", version="1.0.0")


from fastapi import Request

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code} for {request.url.path}")
    return response

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

from .api import backtest, bot, trades
app.include_router(backtest.router, prefix="/api")
app.include_router(bot.router, prefix="/api")
app.include_router(trades.router, prefix="/api")

# Serve Static Files (Frontend)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if dist folder exists (Production)
# Check if dist folder exists (Production)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
logger.info(f"Frontend Dist Path: {frontend_dist}")
logger.info(f"Frontend Dist Exists: {os.path.exists(frontend_dist)}")

if os.path.exists(frontend_dist):
    logger.info(f"Contents of {frontend_dist}: {os.listdir(frontend_dist)}")
    assets_path = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_path):
        logger.info(f"Contents of {assets_path}: {os.listdir(assets_path)}")
    else:
        logger.warning(f"Assets directory not found at {assets_path}")

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
    
    # 2. Start Trading Bot in Background Thread
    # We run it in a thread because it has a blocking while True loop
    bot_thread = threading.Thread(target=trading_bot.main, daemon=True)
    bot_thread.start()
    logger.info("Trading Bot Thread Started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

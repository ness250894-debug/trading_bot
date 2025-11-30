"""
Detailed health check endpoint for monitoring system dependencies.
"""
from fastapi import APIRouter
from typing import Dict
import logging

router = APIRouter()
logger = logging.getLogger("Health")

@router.get("/health/detailed")
async def detailed_health_check() -> Dict:
    """
    Detailed health check for monitoring.
    Returns status of all system dependencies.
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    # Check database
    try:
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        # Simple query to verify connection
        db.conn.execute("SELECT 1").fetchone()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "duckdb"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check exchange connectivity (using global config)
    try:
        from ..core import config
        from ..core.exchange import ExchangeClient
        from ..core.exchange.paper import PaperExchange
        
        if getattr(config, 'DRY_RUN', True):
            client = PaperExchange(config.API_KEY, config.API_SECRET)
        else:
            client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        
        # Try to fetch server time (lightweight check)
        client.exchange.fetch_time()
        
        health_status["components"]["exchange"] = {
            "status": "healthy",
            "exchange": "bybit",
            "mode": "demo" if config.DEMO else "live"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["exchange"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check telegram (optional)
    try:
        from ..core import config
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            health_status["components"]["telegram"] = {
                "status": "configured"
            }
        else:
            health_status["components"]["telegram"] = {
                "status": "not_configured"
            }
    except Exception as e:
        logger.debug(f"Telegram config check failed: {e}")
        health_status["components"]["telegram"] = {
            "status": "not_configured"
        }
    
    # Check bot manager
    try:
        from ..core.bot_manager import bot_manager
        running_bots = bot_manager.get_all_running()
        health_status["components"]["bot_manager"] = {
            "status": "healthy",
            "active_bots": len(running_bots)
        }
    except Exception as e:
        health_status["components"]["bot_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any
import logging
import os
import re
from ..core import config
from ..core.bot import running_event

router = APIRouter()
logger = logging.getLogger("API.Bot")

from ..core.exchange.client import ExchangeClient
# Import PaperExchange conditionally or just import it, it's a class.
from ..core.exchange.paper import PaperExchange

@router.get("/balance")
async def get_balance():
    try:
        # Initialize client based on config
        if getattr(config, 'DRY_RUN', False):
            client = PaperExchange(config.API_KEY, config.API_SECRET)
        else:
            client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
            
        balance = client.fetch_balance()
        return balance
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ConfigUpdate(BaseModel):
    symbol: str
    timeframe: str
    amount_usdt: float
    strategy: str
    dry_run: bool
    
    @validator('amount_usdt')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('amount_usdt must be positive')
        if v > 10000:
            raise ValueError('amount_usdt cannot exceed 10000')
        return v
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v

@router.post("/start")
async def start_bot():
    running_event.set()
    logger.info("Bot started via API")
    return {"status": "success", "message": "Bot started"}

@router.post("/stop")
async def stop_bot():
    running_event.clear()
    logger.info("Bot stopped via API")
    return {"status": "success", "message": "Bot stopped"}

@router.get("/status")
async def get_status():
    # Reload config module to get latest values if they changed on disk (though python caches modules)
    # In production, we'd use a database or a proper config loader.
    # For now, we rely on the process restart for full effect, but we can return what's in memory.
    return {
        "status": "Active" if running_event.is_set() else "Paused",
        "is_running": running_event.is_set(),
        "config": {
            "symbol": config.SYMBOL,
            "timeframe": config.TIMEFRAME,
            "amount_usdt": config.AMOUNT_USDT,
            "strategy": getattr(config, 'STRATEGY', 'mean_reversion'),
            "dry_run": getattr(config, 'DRY_RUN', True)
        }
    }

@router.post("/config")
async def update_config(update: ConfigUpdate):
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'config.py')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Helper to replace variable assignment
        def replace_var(name, value, content):
            # Regex to find "NAME = value" or "NAME = 'value'"
            # We assume simple formatting as in the file
            if isinstance(value, str):
                new_line = f"{name} = '{value}'"
            else:
                new_line = f"{name} = {value}"
            
            # This regex looks for start of line, name, equals, and then anything until end of line (or comment)
            pattern = rf"^{name}\s*=\s*.*"
            
            if re.search(pattern, content, re.MULTILINE):
                return re.sub(pattern, new_line, content, flags=re.MULTILINE)
            else:
                # If not found, append it (fallback)
                return content + f"\n{new_line}"

        # Apply updates
        content = replace_var('TIMEFRAME', update.timeframe, content)
        content = replace_var('AMOUNT_USDT', update.amount_usdt, content)
        content = replace_var('STRATEGY', update.strategy, content)
        content = replace_var('DRY_RUN', update.dry_run, content)
        # Symbol is usually hardcoded or we can update it too
        content = replace_var('SYMBOL', update.symbol, content)

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"status": "success", "message": "Config updated. Please restart the bot."}
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
async def restart_bot():
    """
    Triggers a backend restart by exiting the process.
    The parent run.py script will detect the exit and restart the process.
    """
    logger.info("Restart requested via API.")
    # We use os._exit to ensure immediate exit without cleanup hooks that might delay it
    # But sys.exit(0) is usually cleaner.
    import sys
    import threading
    
    def kill():
        import time
        time.sleep(1) # Give time to return response
        os._exit(0)
        
    threading.Thread(target=kill).start()
    return {"status": "success", "message": "Bot is restarting..."}

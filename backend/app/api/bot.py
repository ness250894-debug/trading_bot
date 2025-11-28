from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
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
    take_profit_pct: float
    stop_loss_pct: float
    parameters: Optional[Dict[str, Any]] = {}
    
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
    try:
        # Fetch balance from exchange
        if getattr(config, 'DRY_RUN', False):
            client = PaperExchange(config.API_KEY, config.API_SECRET)
        else:
            client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        
        balance_data = client.fetch_balance()
        


        # Get USDT balance (free + used)
        usdt_balance = balance_data.get('USDT', {})
        total_balance = usdt_balance.get('total', 0.0)
        free_balance = usdt_balance.get('free', 0.0)
        used_balance = usdt_balance.get('used', 0.0)
        
        # Calculate total PnL from database
        from ..core.database import DuckDBHandler
        db = DuckDBHandler()
        total_pnl = db.get_total_pnl()
        
        # Get active trades count from position
        position = client.fetch_position(config.SYMBOL)
        active_trades = 1 if position.get('size', 0.0) > 0 else 0
        
        return {
            "status": "Active" if running_event.is_set() else "Paused",
            "is_running": running_event.is_set(),
            "balance": {
                "total": total_balance,
                "free": free_balance,
                "used": used_balance
            },
            "total_pnl": total_pnl,
            "active_trades": active_trades,
            "config": {
                "symbol": config.SYMBOL,
                "timeframe": config.TIMEFRAME,
                "amount_usdt": config.AMOUNT_USDT,
                "strategy": getattr(config, 'STRATEGY', 'mean_reversion'),
                "dry_run": getattr(config, 'DRY_RUN', True),
                "take_profit_pct": getattr(config, 'TAKE_PROFIT_PCT', 0.01),
                "stop_loss_pct": getattr(config, 'STOP_LOSS_PCT', 0.005),
                "parameters": getattr(config, 'STRATEGY_PARAMS', {})
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        # Return a fallback status if exchange is unreachable
        return {
            "status": "Active" if running_event.is_set() else "Paused",
            "is_running": running_event.is_set(),
            "balance": {
                "total": 0.0,
                "free": 0.0,
                "used": 0.0
            },
            "total_pnl": 0.0,
            "active_trades": 0,
            "config": {
                "symbol": config.SYMBOL,
                "timeframe": config.TIMEFRAME,
                "amount_usdt": config.AMOUNT_USDT,
                "strategy": getattr(config, 'STRATEGY', 'mean_reversion'),
                "dry_run": getattr(config, 'DRY_RUN', True),
                "take_profit_pct": getattr(config, 'TAKE_PROFIT_PCT', 0.01),
                "stop_loss_pct": getattr(config, 'STOP_LOSS_PCT', 0.005),
                "parameters": getattr(config, 'STRATEGY_PARAMS', {})
            },
            "error": str(e)
        }

@router.post("/config")
async def update_config(update: ConfigUpdate):
    try:
        import json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'config.json')
        
        # Prepare new config data
        new_config = {
            "SYMBOL": update.symbol,
            "TIMEFRAME": update.timeframe,
            "AMOUNT_USDT": update.amount_usdt,
            "STRATEGY": update.strategy,
            "STRATEGY_PARAMS": update.parameters,
            "DRY_RUN": update.dry_run,
            "TAKE_PROFIT_PCT": update.take_profit_pct,
            "STOP_LOSS_PCT": update.stop_loss_pct
        }
        
        # Write to JSON file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4)
            
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

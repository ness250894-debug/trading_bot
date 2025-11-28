from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
import logging
import os
from ..core import config, auth
from ..core.bot_manager import bot_manager
from ..core.database import DuckDBHandler
from ..core.exchange.client import ExchangeClient
from ..core.exchange.paper import PaperExchange

router = APIRouter()
logger = logging.getLogger("API.Bot")
db = DuckDBHandler()

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

@router.get("/balance")
async def get_balance(current_user: dict = Depends(auth.get_current_user)):
    """Get exchange balance."""
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
        raise HTTPException(status_code=500, detail="Failed to fetch balance")

@router.post("/start")
async def start_bot(current_user: dict = Depends(auth.get_current_user)):
    """Start user's bot instance."""
    try:
        user_id = current_user['id']
        
        # Load user's strategy from database
        strategy_config = db.get_user_strategy(user_id)
        
        # If no strategy in DB, use config.json as default
        if not strategy_config:
            strategy_config = {
                "SYMBOL": config.SYMBOL,
                "TIMEFRAME": config.TIMEFRAME,
                "AMOUNT_USDT": config.AMOUNT_USDT,
                "STRATEGY": getattr(config, 'STRATEGY', 'mean_reversion'),
                "STRATEGY_PARAMS": getattr(config, 'STRATEGY_PARAMS', {}),
                "DRY_RUN": getattr(config, 'DRY_RUN', True),
                "TAKE_PROFIT_PCT": config.TAKE_PROFIT_PCT,
                "STOP_LOSS_PCT": config.STOP_LOSS_PCT,
            }
        
        # Start bot instance
        success = bot_manager.start_bot(user_id, strategy_config)
        
        if success:
            logger.info(f"Bot started for user {user_id}")
            return {"status": "success", "message": "Bot started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start bot")
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to start bot")

@router.post("/stop")
async def stop_bot(current_user: dict = Depends(auth.get_current_user)):
    """Stop user's bot instance."""
    try:
        user_id = current_user['id']
        success = bot_manager.stop_bot(user_id)
        
        if success:
            logger.info(f"Bot stopped for user {user_id}")
            return {"status": "success", "message": "Bot stopped"}
        else:
            return {"status": "success", "message": "Bot was not running"}
            
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop bot")

@router.get("/status")
async def get_status(current_user: dict = Depends(auth.get_current_user)):
    """Get user's bot status."""
    try:
        user_id = current_user['id']
        
        # Get bot instance status
        bot_status = bot_manager.get_status(user_id)
        is_running = bot_status['is_running'] if bot_status else False
        
        # Get user's strategy config
        strategy_config = db.get_user_strategy(user_id)
        if not strategy_config:
            # Fallback to config.json
            strategy_config = {
                "symbol": config.SYMBOL,
                "timeframe": config.TIMEFRAME,
                "amount_usdt": config.AMOUNT_USDT,
                "strategy": getattr(config, 'STRATEGY', 'mean_reversion'),
                "dry_run": getattr(config, 'DRY_RUN', True),
                "take_profit_pct": config.TAKE_PROFIT_PCT,
                "stop_loss_pct": config.STOP_LOSS_PCT,
                "parameters": getattr(config, 'STRATEGY_PARAMS', {})
            }
        else:
            # Convert to lowercase keys for response
            strategy_config = {
                "symbol": strategy_config.get('SYMBOL', config.SYMBOL),
                "timeframe": strategy_config.get('TIMEFRAME', config.TIMEFRAME),
                "amount_usdt": strategy_config.get('AMOUNT_USDT', config.AMOUNT_USDT),
                "strategy": strategy_config.get('STRATEGY', 'mean_reversion'),
                "dry_run": strategy_config.get('DRY_RUN', True),
                "take_profit_pct": strategy_config.get('TAKE_PROFIT_PCT', 0.01),
                "stop_loss_pct": strategy_config.get('STOP_LOSS_PCT', 0.005),
                "parameters": strategy_config.get('STRATEGY_PARAMS', {})
            }
        
        # Try to fetch balance
        try:
            if strategy_config["dry_run"]:
                client = PaperExchange(config.API_KEY, config.API_SECRET)
            else:
                client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
            
            balance_data = client.fetch_balance()
            usdt_balance = balance_data.get('USDT', {})
            
            balance_info = {
                "total": usdt_balance.get('total', 0.0),
                "free": usdt_balance.get('free', 0.0),
                "used": usdt_balance.get('used', 0.0)
            }
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")
            balance_info = {"total": 0.0, "free": 0.0, "used": 0.0}
        
        # Get PnL from database for this user
        total_pnl = db.get_total_pnl(user_id=current_user['id'])
        
        return {
            "status": "Active" if is_running else "Stopped",
            "is_running": is_running,
            "balance": balance_info,
            "total_pnl": total_pnl,
            "active_trades": 0,  # TODO: Get from bot instance
            "config": strategy_config
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        # Return minimal fallback status
        return {
            "status": "Error",
            "is_running": False,
            "balance": {"total": 0.0, "free": 0.0, "used": 0.0},
            "total_pnl": 0.0,
            "active_trades": 0,
            "config": {},
            "error": "Failed to fetch status"
        }

@router.post("/config")
async def update_config(update: ConfigUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update user's strategy configuration."""
    try:
        user_id = current_user['id']
        
        # Prepare config dict
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
        
        # Save to database
        success = db.save_user_strategy(user_id, new_config)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
        # If bot is running, restart it with new config
        bot_status = bot_manager.get_status(user_id)
        if bot_status and bot_status['is_running']:
            bot_manager.restart_bot(user_id, new_config)
            return {"status": "success", "message": "Config updated and bot restarted"}
        else:
            return {"status": "success", "message": "Config updated"}
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@router.post("/restart")
async def restart_bot(current_user: dict = Depends(auth.get_current_user)):
    """Restart user's bot with current configuration."""
    try:
        user_id = current_user['id']
        
        # Load current strategy
        strategy_config = db.get_user_strategy(user_id)
        
        if not strategy_config:
            raise HTTPException(status_code=400, detail="No configuration found. Please update config first.")
        
        # Restart bot
        success = bot_manager.restart_bot(user_id, strategy_config)
        
        if success:
            return {"status": "success", "message": "Bot restarted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to restart bot")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart bot")

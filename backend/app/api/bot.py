from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
import logging
import os
from ..core import config, auth
from ..core.bot_manager import bot_manager
from ..core.database import DuckDBHandler
from ..core.exchange import ExchangeClient
from ..core.exchange.paper import PaperExchange
from ..core.rate_limit import limiter
from starlette.requests import Request

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

class RiskProfileUpdate(BaseModel):
    max_daily_loss: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_position_size: Optional[float] = None
    max_open_positions: Optional[int] = None
    stop_trading_on_breach: bool = True

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

from datetime import datetime

@router.post("/start")
@limiter.limit("5/minute")
async def start_bot(request: Request, symbol: Optional[str] = None, current_user: dict = Depends(auth.get_current_user)):
    """Start user's bot instance for a specific symbol (or default from config)."""
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
            
        # Enforce Billing for Live Trading
        is_dry_run = strategy_config.get("DRY_RUN", True)
        is_admin = current_user.get('is_admin', False)
        
        if not is_dry_run and not is_admin:
            subscription = db.get_subscription(user_id)
            is_valid_pro = False
            
            if subscription and subscription['status'] == 'active':
                # Check expiration
                if subscription['expires_at'] and subscription['expires_at'] > datetime.now():
                    # Check plan type (assuming all paid plans start with 'pro')
                    if subscription['plan_id'].startswith('pro'):
                        is_valid_pro = True
            
            if not is_valid_pro:
                raise HTTPException(
                    status_code=403, 
                    detail="Live trading requires an active Pro subscription. Please upgrade your plan."
                )

        # Enforce Free Plan Limits
        # Check if user is on Free plan
        subscription = db.get_subscription(user_id)
        is_free_plan = True
        if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
            is_free_plan = False
        
        if is_admin:
            is_free_plan = False

        if is_free_plan:
            # 1. Force Dry Run
            if not strategy_config.get("DRY_RUN", True):
                 raise HTTPException(status_code=403, detail="Free plan only supports Dry Run mode.")
            
            # 2. Force Default Strategy
            if strategy_config.get("STRATEGY") != 'mean_reversion':
                # We could force it here, but better to fail if they try to run something else
                # Or just override it silently? User asked to "cannot choose strategy".
                # Let's override it to be safe, but maybe warn?
                # Actually, let's just enforce it.
                strategy_config["STRATEGY"] = 'mean_reversion'
                # Also reset params to default? Maybe not strictly necessary if strategy is fixed.
            
            # 3. Limit to 1 Bot
            # Check if any bot is already running
            running_bots = bot_manager.get_status(user_id)
            if running_bots:
                # running_bots can be a dict of {symbol: status} or a single status dict
                # If it's a dict of dicts, check if any is running
                any_running = False
                if isinstance(running_bots, dict):
                    # Check if it's a multi-instance response (keys are symbols)
                    # A single instance status also has keys like 'user_id', 'is_running'
                    if 'is_running' in running_bots:
                         if running_bots['is_running']:
                             any_running = True
                    else:
                        # It's a dict of symbols
                        for sym, status in running_bots.items():
                            if status.get('is_running'):
                                any_running = True
                                break
                
                if any_running:
                     raise HTTPException(status_code=403, detail="Free plan is limited to 1 active bot.")

        
        # Start bot instance with optional symbol parameter
        success = bot_manager.start_bot(user_id, strategy_config, symbol=symbol)
        
        if success:
            logger.info(f"Bot started for user {user_id}")
            return {"status": "success", "message": "Bot started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start bot")
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to start bot")

@router.post("/stop")
@limiter.limit("10/minute")
async def stop_bot(request: Request, symbol: Optional[str] = None, current_user: dict = Depends(auth.get_current_user)):
    """Stop user's bot instance. If symbol is None, stops all instances."""
    try:
        user_id = current_user['id']
        success = bot_manager.stop_bot(user_id, symbol=symbol)
        
        if success:
            logger.info(f"Bot stopped for user {user_id}")
            return {"status": "success", "message": "Bot stopped"}
        else:
            return {"status": "success", "message": "Bot was not running"}
            
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop bot")

@router.get("/status")
async def get_status(symbol: Optional[str] = None, current_user: dict = Depends(auth.get_current_user)):
    """Get user's bot status. If symbol is None, returns all instances."""
    try:
        user_id = current_user['id']
        
        # Get bot instance status (may return dict of instances or single instance)
        bot_status = bot_manager.get_status(user_id, symbol=symbol)
        
        # Handle multi-instance response (dict of {symbol: status})
        if bot_status and isinstance(bot_status, dict) and not bot_status.get('is_running'):
            # This is a multi-instance dict, check if any are running
            is_running = any(inst.get('is_running', False) for inst in bot_status.values())
        else:
            is_running = bot_status.get('is_running', False) if bot_status else False
        
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
            "active_trades": bot_status.get('active_trades', 0) if bot_status and isinstance(bot_status, dict) else 0,
            "instances": bot_status if bot_status and isinstance(bot_status, dict) else {},
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
            "instances": {},
            "config": {},
            "error": "Failed to fetch status"
        }

@router.post("/config")
@limiter.limit("5/minute")
async def update_config(request: Request, update: ConfigUpdate, current_user: dict = Depends(auth.get_current_user)):
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
        
        # Enforce Free Plan Limits on Config Update
        is_admin = current_user.get('is_admin', False)
        if not is_admin:
            subscription = db.get_subscription(user_id)
            is_free_plan = True
            if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
                is_free_plan = False
            
            if is_free_plan:
                # Force Strategy to Default
                if new_config["STRATEGY"] != 'mean_reversion':
                     # We can either raise error or force it. 
                     # "cannot choose strategy" implies they shouldn't be able to set it.
                     # Let's force it to ensure compliance even if frontend allows it.
                     new_config["STRATEGY"] = 'mean_reversion'
                     # We might want to notify user, but API just returns success.
                     # Frontend should handle the UI part.

        
        # Save to database
        success = db.save_user_strategy(user_id, new_config)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
        # If bot is running, restart it with new config
        bot_status = bot_manager.get_status(user_id, symbol=update.symbol)
        is_bot_running = False
        if bot_status:
            # Handle both single instance and multi-instance response
            if isinstance(bot_status, dict) and 'is_running' in bot_status:
                is_bot_running = bot_status['is_running']
        
        if is_bot_running:
            bot_manager.restart_bot(user_id, new_config, symbol=update.symbol)
            return {"status": "success", "message": "Config updated and bot restarted"}
        else:
            return {"status": "success", "message": "Config updated"}
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@router.post("/restart")
@limiter.limit("5/minute")
async def restart_bot(request: Request, symbol: Optional[str] = None, current_user: dict = Depends(auth.get_current_user)):
    """Restart user's bot with current configuration for a specific symbol."""
    try:
        user_id = current_user['id']
        
        # Load current strategy
        strategy_config = db.get_user_strategy(user_id)
        
        if not strategy_config:
            raise HTTPException(status_code=400, detail="No configuration found. Please update config first.")
        
        # Restart bot with optional symbol parameter
        success = bot_manager.restart_bot(user_id, strategy_config, symbol=symbol)
        
        if success:
            return {"status": "success", "message": "Bot restarted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to restart bot")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart bot")

# Bot Configurations Endpoints
class BotConfigCreate(BaseModel):
    symbol: str
    strategy: str
    timeframe: str
    amount_usdt: float
    take_profit_pct: float
    stop_loss_pct: float
    parameters: Optional[Dict[str, Any]] = {}
    dry_run: bool = True
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v
    
    @validator('amount_usdt')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('amount_usdt must be positive')
        if v > 10000:
            raise ValueError('amount_usdt cannot exceed 10000')
        return v

@router.get("/bot-configs")
@limiter.limit("60/minute")
async def get_bot_configs(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get all bot configurations for current user."""
    try:
        configs = db.get_bot_configs(current_user['id'])
        return {"configs": configs}
    except Exception as e:
        logger.error(f"Error getting bot configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bot configurations")

@router.post("/bot-configs")
@limiter.limit("20/minute")
async def create_bot_config(request: Request, config: BotConfigCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a new bot configuration."""
    try:
        config_id = db.create_bot_config(current_user['id'], config.dict())
        
        if config_id:
            # Get the created config
            created_config = db.get_bot_config(current_user['id'], config_id)
            return {"status": "success", "config": created_config}
        else:
            raise HTTPException(status_code=400, detail="Failed to create bot configuration. Symbol may already exist.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bot config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bot-configs/{config_id}")
@limiter.limit("20/minute")
async def update_bot_config(request: Request, config_id: int, config: BotConfigCreate, current_user: dict = Depends(auth.get_current_user)):
    """Update a bot configuration."""
    try:
        # Verify config belongs to user
        existing = db.get_bot_config(current_user['id'], config_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Bot configuration not found")
        
        success = db.update_bot_config(current_user['id'], config_id, config.dict())
        
        if success:
            updated_config = db.get_bot_config(current_user['id'], config_id)
            return {"status": "success", "config": updated_config}
        else:
            raise HTTPException(status_code=500, detail="Failed to update bot configuration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bot-configs/{config_id}")
@limiter.limit("20/minute")
async def delete_bot_config(request: Request, config_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a bot configuration."""
    try:
        # Verify config belongs to user
        existing = db.get_bot_config(current_user['id'], config_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Bot configuration not found")
        
        # Stop bot if running for this symbol
        symbol = existing['symbol']
        bot_status = bot_manager.get_status(current_user['id'], symbol)
        if bot_status and bot_status.get('is_running'):
            bot_manager.stop_bot(current_user['id'], symbol)
        
        success = db.delete_bot_config(current_user['id'], config_id)
        
        if success:
            return {"status": "success", "message": "Bot configuration deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete bot configuration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bot config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trade Journal Endpoints
class TradeNoteCreate(BaseModel):
    notes: str
    tags: Optional[str] = None

@router.get("/trades")
async def get_trades(limit: int = 100, offset: int = 0, current_user: dict = Depends(auth.get_current_user)):
    """Get user's trade history with notes."""
    try:
        trades_df = db.get_trades(current_user['id'], limit, offset)
        if trades_df.empty:
            return {"trades": []}
        
        # Convert timestamps to string
        trades = trades_df.to_dict(orient='records')
        for trade in trades:
            if isinstance(trade.get('timestamp'), (datetime, pd.Timestamp)):
                trade['timestamp'] = trade['timestamp'].isoformat()
                
        return {"trades": trades}
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trades")

@router.get("/trades/{trade_id}/notes")
@limiter.limit("60/minute")
async def get_trade_note(request: Request, trade_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Get note for a specific trade."""
    try:
        note = db.get_trade_note(current_user['id'], trade_id)
        if note:
            return {"note": note}
        else:
            return {"note": None}
    except Exception as e:
        logger.error(f"Error getting trade note: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trade note")

@router.post("/trades/{trade_id}/notes")
@limiter.limit("20/minute")
async def save_trade_note(request: Request, trade_id: int, note_data: TradeNoteCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create or update note for a trade."""
    try:
        note_id = db.save_trade_note(current_user['id'], trade_id, note_data.notes, note_data.tags)
        
        if note_id:
            note = db.get_trade_note(current_user['id'], trade_id)
            return {"status": "success", "note": note}
        else:
            raise HTTPException(status_code=500, detail="Failed to save trade note")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving trade note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trades/notes/{note_id}")
@limiter.limit("20/minute")
async def delete_trade_note(request: Request, note_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a trade note."""
    try:
        success = db.delete_trade_note(current_user['id'], note_id)
        
        if success:
            return {"status": "success", "message": "Trade note deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete trade note")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trade note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Watchlist Endpoints
class WatchlistAdd(BaseModel):
    symbol: str
    notes: Optional[str] = None
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v

@router.get("/watchlist")
@limiter.limit("60/minute")
async def get_watchlist(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get user's watchlist."""
    try:
        watchlist = db.get_watchlist(current_user['id'])
        return {"watchlist": watchlist}
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")

@router.post("/watchlist")
@limiter.limit("20/minute")
async def add_to_watchlist_endpoint(request: Request, data: WatchlistAdd, current_user: dict = Depends(auth.get_current_user)):
    """Add symbol to watchlist."""
    try:
        watchlist_id = db.add_to_watchlist(current_user['id'], data.symbol, data.notes)
        
        if watchlist_id:
            return {"status": "success", "message": f"Added {data.symbol} to watchlist"}
        else:
            raise HTTPException(status_code=400, detail="Symbol may already be in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlist/{symbol}")
@limiter.limit("20/minute")
async def remove_from_watchlist_endpoint(request: Request, symbol: str, current_user: dict = Depends(auth.get_current_user)):
    """Remove symbol from watchlist."""
    try:
        success = db.remove_from_watchlist(current_user['id'], symbol)
        
        if success:
            return {"status": "success", "message": f"Removed {symbol} from watchlist"}
        else:
            raise HTTPException(status_code=500, detail="Failed to remove from watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Price Alerts Endpoints
class AlertCreate(BaseModel):
    symbol: str
    condition: str
    price_target: float
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v
    
    @validator('condition')
    def condition_must_be_valid(cls, v):
        if v not in ['above', 'below']:
            raise ValueError('condition must be "above" or "below"')
        return v
    
    @validator('price_target')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('price_target must be positive')
        return v

@router.get("/alerts")
@limiter.limit("60/minute")
async def get_alerts(request: Request, active_only: bool = True, current_user: dict = Depends(auth.get_current_user)):
    """Get user's price alerts."""
    try:
        alerts = db.get_alerts(current_user['id'], active_only=active_only)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

@router.post("/alerts")
@limiter.limit("20/minute")
async def create_alert(request: Request, data: AlertCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a price alert."""
    try:
        alert_id = db.create_alert(current_user['id'], data.symbol, data.condition, data.price_target)
        
        if alert_id:
            return {"status": "success", "alert_id": alert_id, "message": f"Alert created for {data.symbol}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create alert")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/{alert_id}")
@limiter.limit("20/minute")
async def delete_alert(request: Request, alert_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a price alert."""
    try:
        success = db.delete_alert(current_user['id'], alert_id)
        
        if success:
            return {"status": "success", "message": "Alert deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete alert")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Preferences Endpoints
class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    widgets_enabled: Optional[list] = None
    
    @validator('theme')
    def theme_must_be_valid(cls, v):
        if v and v not in ['dark', 'light']:
            raise ValueError('theme must be "dark" or "light"')
        return v

@router.get("/preferences")
@limiter.limit("60/minute")
async def get_preferences(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get user's dashboard preferences."""
    try:
        prefs = db.get_preferences(current_user['id'])
        return {"preferences": prefs}
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")

@router.put("/preferences")
@limiter.limit("20/minute")
async def update_preferences(request: Request, data: PreferencesUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update user's dashboard preferences."""
    try:
        success = db.save_preferences(
            current_user['id'],
            theme=data.theme,
            layout_config=data.layout_config,
            widgets_enabled=data.widgets_enabled
        )
        
        if success:
            prefs = db.get_preferences(current_user['id'])
            return {"status": "success", "preferences": prefs}
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Backtest Templates Endpoints
class TemplateCreate(BaseModel):
    name: str
    symbol: str
    timeframe: str
    strategy: str
    parameters: Optional[Dict[str, Any]] = {}
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if '/' not in v:
            raise ValueError('symbol must contain /')
        return v

@router.get("/backtest-templates")
@limiter.limit("60/minute")
async def get_templates(request: Request, current_user: dict = Depends(auth.get_current_user)):
    """Get user's backtest templates."""
    try:
        templates = db.get_templates(current_user['id'])
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")

@router.post("/backtest-templates")
@limiter.limit("20/minute")
async def create_template(request: Request, data: TemplateCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a backtest template."""
    try:
        template_id = db.create_template(
            current_user['id'],
            data.name,
            data.symbol,
            data.timeframe,
            data.strategy,
            data.parameters
        )
        
        if template_id:
            return {"status": "success", "template_id": template_id, "message": f"Template '{data.name}' created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create template")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/backtest-templates/{template_id}")
@limiter.limit("20/minute")
async def delete_template(request: Request, template_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a backtest template."""
    try:
        success = db.delete_template(current_user['id'], template_id)
        
        if success:
            return {"status": "success", "message": "Template deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete template")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-profile")
async def get_risk_profile(current_user: dict = Depends(auth.get_current_user)):
    """Get user's risk profile."""
    try:
        profile = db.get_risk_profile(current_user['id'])
        return {"profile": profile}
    except Exception as e:
        logger.error(f"Error fetching risk profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk profile")

@router.put("/risk-profile")
@limiter.limit("10/minute")
async def update_risk_profile(request: Request, profile_data: RiskProfileUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update user's risk profile."""
    try:
        success = db.update_risk_profile(current_user['id'], profile_data.dict(exclude_unset=True))
        
        if success:
            return {"status": "success", "message": "Risk profile updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update risk profile")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

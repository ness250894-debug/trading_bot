import logging
import logging.config
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException

from ..database import DuckDBHandler
from ..bot_manager import bot_manager
from .. import config
from ..exchange import ExchangeClient
from ..exchange.paper import PaperExchange
from ..encryption import EncryptionHelper
from ..client_manager import client_manager
from ..socket_manager import socket_manager
import asyncio

logger = logging.getLogger("Core.BotService")

class BotService:
    def __init__(self):
        self.db = DuckDBHandler()
        self.encryption = EncryptionHelper()

    def get_exchange_balance(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fetch current exchange balance."""
        try:
            if dry_run:
                client = PaperExchange(config.API_KEY, config.API_SECRET)
            else:
                client = ExchangeClient(config.API_KEY, config.API_SECRET)
            return client.fetch_balance()
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch balance")

    def _enforce_subscription(self, user_id: int, strategy_config: Dict[str, Any], is_admin: bool = False):
        """Enforce subscription limits (Pro vs Free)."""
        is_dry_run = strategy_config.get("DRY_RUN", True)
        
        # 1. Start check: Live Trading requires Pro
        if not is_dry_run and not is_admin:
            subscription = self.db.get_subscription(user_id)
            is_valid_pro = False
            if subscription and subscription['status'] == 'active':
                if subscription['expires_at'] and subscription['expires_at'] > datetime.now():
                    if subscription['plan_id'].startswith('pro'):
                        is_valid_pro = True
            
            if not is_valid_pro:
                raise HTTPException(
                    status_code=403, 
                    detail="Live trading requires an active Pro subscription. Please upgrade your plan."
                )

        # 2. Free Plan Limits
        if not is_admin:
            subscription = self.db.get_subscription(user_id)
            is_free_plan = True
            if subscription and subscription['status'] == 'active' and not subscription['plan_id'].startswith('free'):
                is_free_plan = False
            
            if is_free_plan:
                # Force Dry Run
                if not strategy_config.get("DRY_RUN", True):
                     raise HTTPException(status_code=403, detail="Free plan only supports Dry Run mode.")
                
                # Force Strategy
                if strategy_config.get("STRATEGY") != 'mean_reversion':
                    strategy_config["STRATEGY"] = 'mean_reversion'
                
                # Limit active bots
                running_bots = bot_manager.get_status(user_id)
                any_running = False
                if running_bots:
                    if isinstance(running_bots, dict):
                        if 'is_running' in running_bots:
                             if running_bots['is_running']: any_running = True
                        else:
                            # Multi-instance dict
                            for status in running_bots.values():
                                if status.get('is_running'):
                                    any_running = True
                                    break
                    
                    if any_running:
                         raise HTTPException(status_code=403, detail="Free plan is limited to 1 active bot.")
        return strategy_config

    def start_bot(self, user_id: int, config_id: Optional[int] = None, symbol: Optional[str] = None) -> bool:
        """Start a bot instance."""
        if config_id:
            strategy_config = self.db.get_bot_config(user_id, config_id)
            if not strategy_config:
                raise HTTPException(status_code=404, detail="Bot configuration not found")
            
            # Map DB keys to internal format
            strategy_config.update({
                'SYMBOL': strategy_config['symbol'],
                'TIMEFRAME': strategy_config['timeframe'],
                'AMOUNT_USDT': strategy_config['amount_usdt'],
                'STRATEGY': strategy_config['strategy'],
                'STRATEGY_PARAMS': strategy_config.get('parameters', {}),
                'DRY_RUN': strategy_config['dry_run'],
                'TAKE_PROFIT_PCT': strategy_config['take_profit_pct'],
                'STOP_LOSS_PCT': strategy_config['stop_loss_pct'],
                'LEVERAGE': strategy_config.get('leverage', 10.0),
            })
        else:
            # Legacy/Single Bot Mode
            strategy_config = self.db.get_user_strategy(user_id)
            if not strategy_config:
                # Default config
                strategy_config = {
                    "SYMBOL": config.SYMBOL,
                    "TIMEFRAME": config.TIMEFRAME,
                    "AMOUNT_USDT": config.AMOUNT_USDT,
                    "STRATEGY": getattr(config, 'STRATEGY', 'mean_reversion'),
                    "STRATEGY_PARAMS": getattr(config, 'STRATEGY_PARAMS', {}),
                    "DRY_RUN": getattr(config, 'DRY_RUN', True),
                    "TAKE_PROFIT_PCT": config.TAKE_PROFIT_PCT,
                    "STOP_LOSS_PCT": config.STOP_LOSS_PCT,
                    "LEVERAGE": getattr(config, 'LEVERAGE', 10.0),
                }

        # Enforce Limits
        is_admin = self.db.get_user_by_id(user_id).get('is_admin', False)
        strategy_config = self._enforce_subscription(user_id, strategy_config, is_admin)

        success = bot_manager.start_bot(user_id, strategy_config, config_id=config_id)
        
        if success:
             # Broadcast update
             asyncio.create_task(self.broadcast_status_update(user_id))
             
        return success

    def stop_bot(self, user_id: int, config_id: Optional[int] = None, symbol: Optional[str] = None) -> bool:
        """Stop a bot instance."""
        success = bot_manager.stop_bot(user_id, config_id=config_id, symbol=symbol)
        if success:
             # Broadcast update
             asyncio.create_task(self.broadcast_status_update(user_id))
        return success

    def get_bot_status(self, user_id: int, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate bot status, PnL, and balance info."""
        # Get runtime status
        bot_status = bot_manager.get_status(user_id, symbol=symbol)
        
        # Determine global running state
        is_running = False
        if bot_status:
            if isinstance(bot_status, dict) and 'is_running' in bot_status:
                is_running = bot_status['is_running']
            elif isinstance(bot_status, dict):
                 is_running = any(inst.get('is_running', False) for inst in bot_status.values())

        # Get Config (Legacy support mainly)
        strategy_config = self.db.get_user_strategy(user_id) or {}
        
        # Balance
        try:
            # Check if any running instance is live, else assume dry run from global/first config
            # Simpler: just check global switch or config
            dry_run = strategy_config.get('DRY_RUN', True)
            balance_data = self.get_exchange_balance(dry_run=dry_run)
            usdt_balance = balance_data.get('USDT', {})
            balance_info = {
                "total": usdt_balance.get('total', 0.0),
                "free": usdt_balance.get('free', 0.0),
                "used": usdt_balance.get('used', 0.0)
            }
        except Exception:
            balance_info = {"total": 0.0, "free": 0.0, "used": 0.0}

        # PnL
        total_pnl = self.db.get_total_pnl(user_id=user_id)
        
        # Unrealized PnL from memory
        total_unrealized_pnl = 0.0
        if bot_status:
             if isinstance(bot_status, dict) and 'is_running' not in bot_status:
                 for inst in bot_status.values():
                     total_unrealized_pnl += inst.get('pnl', 0.0)
             else:
                 total_unrealized_pnl = bot_status.get('pnl', 0.0)

        return {
            "status": "Active" if is_running else "Stopped",
            "is_running": is_running,
            "balance": balance_info,
            "total_pnl": total_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "active_trades": bot_status.get('active_trades', 0) if isinstance(bot_status, dict) else 0,
            "instances": bot_status if isinstance(bot_status, dict) else {},
            "config": strategy_config 
        }

    def create_quick_scalp_bot(self, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """Create a default scalping bot."""
        # Check limits
        if not is_admin:
            sub = self.db.get_subscription(user_id)
            is_free = True
            if sub and sub['status'] == 'active' and not sub['plan_id'].startswith('free'):
                is_free = False
            
            if is_free:
                existing = self.db.get_bot_configs(user_id)
                if len(existing) >= 1:
                    raise HTTPException(status_code=403, detail="Free plan limit reached.")

        config_data = {
            "symbol": "BTC/USDT",
            "strategy": "momentum",
            "timeframe": "1m",
            "amount_usdt": 100.0,
            "take_profit_pct": 0.03,
            "stop_loss_pct": 0.03,
            "dry_run": True,
            "parameters": {
                "roc_period": 1,
                "rsi_period": 2,
                "rsi_min": 10,
                "rsi_max": 90
            }
        }
        
        config_id = self.db.create_bot_config(user_id, config_data)
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create config")
            
        return self.db.get_bot_config(user_id, config_id)

    def delete_bot_config(self, user_id: int, config_id: int) -> bool:
        """Delete bot config and close positions."""
        existing = self.db.get_bot_config(user_id, config_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Config not found")

        symbol = existing['symbol']
        
        # 1. Close Open Positions
        self._close_position_safely(user_id, existing)
        
        # 2. Stop Bot if running
        self.stop_bot(user_id, config_id=config_id, symbol=symbol)
        
        # 3. Delete Config
        return self.db.delete_bot_config(user_id, config_id)

    async def broadcast_status_update(self, user_id: int):
        """Emit current status to WS."""
        try:
            status = self.get_bot_status(user_id)
            await socket_manager.broadcast({
                "type": "status_update",
                "data": status
            }, user_id=user_id)
        except Exception as e:
            logger.error(f"WS Broadcast failed: {e}")

    def _close_position_safely(self, user_id: int, config_data: Dict[str, Any]):
        """Attempt to close position on exchange."""
        try:
            exchange_name = config_data.get('exchange', 'bybit')
            symbol = config_data['symbol']
            
            # Get Keys
            api_key_data = self.db.get_api_key(user_id, exchange_name)
            api_key, api_secret = None, None
            
            if api_key_data:
                api_key = self.encryption.decrypt(api_key_data['api_key_encrypted'])
                api_secret = self.encryption.decrypt(api_key_data['api_secret_encrypted'])
            
            if not api_key and exchange_name == 'bybit':
                api_key = config.API_KEY
                api_secret = config.API_SECRET

            if api_key and api_secret:
                client = client_manager.get_client(
                    user_id=user_id,
                    api_key=api_key,
                    api_secret=api_secret,
                    dry_run=config_data.get('dry_run', True),
                    exchange=exchange_name
                )
                
                position = client.fetch_position(symbol)
                size = float(position.get('size', 0.0))
                
                if size > 0:
                    logger.info(f"Closing position for {symbol} (Size: {size})")
                    side = position.get('side', '').lower()
                    close_side = 'sell' if side == 'buy' else 'buy'
                    
                    client.create_order(
                        symbol=symbol,
                        order_type='market',
                        side=close_side,
                        amount=size
                    )
        except Exception as e:
            logger.error(f"Failed to close position for {config_data.get('symbol')}: {e}")
            # Non-blocking error

bot_service = BotService()

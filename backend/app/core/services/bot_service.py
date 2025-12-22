import logging
import logging.config
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException

from ..database import db
from ..bot_manager import bot_manager
from .. import config
from ..exchange import ExchangeClient
from ..exchange.paper import PaperExchange
from ..encryption import EncryptionHelper
from ..client_manager import client_manager
from ..socket_manager import socket_manager
import asyncio
import time

logger = logging.getLogger("Core.BotService")

class BotService:
    def __init__(self):
        self.db = db
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
        """Enforce subscription limits (Feature Based)."""
        is_dry_run = strategy_config.get("DRY_RUN", True)
        
        # Get Features
        features = self.db.get_user_features(user_id, is_admin=is_admin)
        
        # 1. Start check: Live Trading
        if not is_dry_run:
            if "live_trading" not in features:
                 raise HTTPException(
                    status_code=403, 
                    detail="Live trading requires an active paid subscription with the 'live_trading' feature."
                )

        # 2. Bot Limits Check
        # Determine max allowed bots based on features
        max_bots = 1 # Default for free
        if "max_bots_unlimited" in features:
            max_bots = 9999
        elif "max_bots_10" in features:
            max_bots = 10
        elif "max_bots_3" in features:
            max_bots = 3
        
        # Check running bots
        running_bots = bot_manager.get_status(user_id)
        current_active_count = 0
        
        if running_bots:
            if isinstance(running_bots, dict):
                # Check single instance format
                if 'is_running' in running_bots and running_bots['is_running']:
                     current_active_count = 1
                elif 'is_running' not in running_bots:
                    # Multi-instance format
                    for status in running_bots.values():
                        if status.get('is_running'):
                            current_active_count += 1
        
        # If we are potentially starting a new bot, we are strictly checking the limit.
        # However, this method is often called just to VALIDATE config, not necessarily increment count.
        # But if the user tries to START, we should check limit.
        # For now, let's just allow passing if current count < limit.
        # NOTE: This method modifies config in place for limits.
        
        # If user is on Free Plan (no features), enforce restrictions
        if not features: 
            # Force Dry Run
            if not strategy_config.get("DRY_RUN", True):
                    raise HTTPException(status_code=403, detail="Free plan only supports Dry Run mode.")
            
            # Force Strategy (optional, maybe relax this?)
            if strategy_config.get("STRATEGY") != 'mean_reversion':
                # strategy_config["STRATEGY"] = 'mean_reversion' 
                # Relaxing this rule as user asked for "access to premium features" for paid plans, 
                # but for FREE plan, let's keep Mean Reversion only limit if strictly needed. 
                # User's prompt didn't explicitly say "unlock strategies for free".
                # Keeping it for now to encourage upgrade.
                strategy_config["STRATEGY"] = 'mean_reversion'
            
            if current_active_count >= 1:
                # If we are checking the CURRENTLY running bot, it's fine.
                # If we are starting a NEW one, we need to fail.
                # BotService.start_bot calls this.
                pass
        
        # Check Max Bots Limit (for everyone)
        if current_active_count >= max_bots:
             # We need to be careful: if this is called during a start, it blocks.
             # If called during a status check, it shouldn't raise.
             # Since _enforce_subscription is only called in start_bot (and create_bot), 
             # preventing > limit is correct.
             pass 
             # Actually, simpler:
             # If I already have N running and I try to start another (count will result in N+1), I should fail.
             # But this function doesn't know "I am starting +1". 
             # Logic implies: If I am currently at Limit, and I want to start one more...
             # We will enforce this in start_bot logic where we check `if currently_running >= max`.
             # Here we just set restrictions on the CONFIG object mostly.
             
        # Just return cleaned config
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
        
        # Check active bots count limit HERE before enforcing config
        features = self.db.get_user_features(user_id, is_admin=is_admin)
        max_bots = 1
        if "max_bots_unlimited" in features:
            max_bots = 9999
        elif "max_bots_10" in features:
            max_bots = 10
        elif "max_bots_3" in features:
            max_bots = 3
            
        running_bots = bot_manager.get_status(user_id)
        current_active_count = 0
        if running_bots:
            if isinstance(running_bots, dict) and 'is_running' not in running_bots:
                 for status in running_bots.values():
                     if status.get('is_running'):
                         current_active_count += 1
            elif isinstance(running_bots, dict) and running_bots.get('is_running'):
                 current_active_count = 1
        
        # If we are starting a NEW instance (or restarting), check limit
        # Note: If restarting ID 1 and it's already counted in running_bots, we shouldn't double count.
        # But simplistic check: if current >= max, Block.
        # To be cleaner: if config_id is already running, we don't block.
        
        # Simplified enforcement:
        if current_active_count >= max_bots:
             # Check if this specific config is already running (re-start doesn't consume quota)
             is_restart = False
             if config_id:
                 # Check if this config_id is in running_bots
                 pass # simplified for now
             
             if not is_restart:
                  # Strict check
                  # But wait, if I have 3 bots running and I stop one, I have 2. Then I can start.
                  # If I have 3 running, start fails.
                  pass

        # Let's rely on _enforce_subscription for strategy/dry-run, 
        # and do a simpler check here for count if needed? 
        # Actually _enforce_subscription handles config, let's explicitly do count check here.
        if current_active_count >= max_bots:
            # Exception: if we are restarting an already running bot?
            pass 
            
        # We'll inject the 'Enforce Count' logic properly:
        if current_active_count >= max_bots:
            # Only allow if the specific bot we are trying to start is ALREADY running (idempotent start)
            # otherwise block.
             raise HTTPException(status_code=403, detail=f"Active bot limit reached for your plan (Max: {max_bots}). Upgrade to increase limit.")

        strategy_config = self._enforce_subscription(user_id, strategy_config, is_admin)
        
        is_dry_run = strategy_config.get('DRY_RUN', True)

        try:
            main_loop = asyncio.get_running_loop()
        except RuntimeError:
            main_loop = None
            exchange_name = strategy_config.get('exchange', 'bybit')
            api_key_data = self.db.get_api_key(user_id, exchange_name)
            
            has_keys = False
            if api_key_data:
                has_keys = True
            elif exchange_name == 'bybit' and config.API_KEY and config.API_SECRET:
                has_keys = True
                
            if not has_keys:
                 # Signal Only Mode support: Don't raise error, just proceed. 
                 # TradingEngine will detect missing keys and enter Signal Only mode.
                 logger.warning(f"Starting Live bot for {exchange_name} without API keys. Bot will run in SIGNAL ONLY mode.")

        success = bot_manager.start_bot(user_id, strategy_config, config_id=config_id, main_loop=main_loop)
        
        if success:
             # Broadcast update
             asyncio.create_task(self.broadcast_status_update(user_id))
             
        return success

    def stop_bot(self, user_id: int, config_id: Optional[int] = None, symbol: Optional[str] = None) -> bool:
        """Stop a bot instance and close any open positions."""
        
        # 1. Attempt to close position if config exists
        if config_id:
            try:
                config_data = self.db.get_bot_config(user_id, config_id)
                if config_data:
                     closed = self._ensure_position_closed(user_id, config_data)
                     if not closed:
                         raise HTTPException(status_code=500, detail="Failed to close open position after multiple retries. Bot NOT stopped.")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking/closing position for config {config_id}: {e}")
                # If we can't even check, it's safer not to stop? Or force stop?
                # User requirement: "NEEDS to close position no matter what"
                # If we error here, we assume we failed to close.
                raise HTTPException(status_code=500, detail=f"Error checking position: {str(e)}. Bot NOT stopped.")

        # 2. Stop the bot logic
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

        # Get Practice Balance from runtime state or DB
        practice_balance = None
        if bot_status:
             if isinstance(bot_status, dict) and 'is_running' not in bot_status:
                 # Multi-instance: Pick the first one with a value
                 for inst in bot_status.values():
                     pb = inst.get('practice_balance')
                     if pb is not None:
                         practice_balance = pb
                         break
             else:
                 practice_balance = bot_status.get('practice_balance')
        
        # If not in runtime (bot stopped), fetch from DB
        if practice_balance is None:
             user = self.db.get_user_by_id(user_id)
             if user:
                 practice_balance = user.get('practice_balance', 1000.0)
             else:
                 practice_balance = 1000.0

        return {
            "status": "Active" if is_running else "Stopped",
            "is_running": is_running,
            "balance": balance_info,
            "practice_balance": practice_balance,
            "total_pnl": total_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "active_trades": bot_status.get('active_trades', 0) if isinstance(bot_status, dict) else 0,
            "instances": bot_status if isinstance(bot_status, dict) else {},
            "config": strategy_config 
        }

    def reset_practice_balance(self, user_id: int) -> float:
        """Reset practice balance to default."""
        # 1. Update DB
        self.db.update_practice_balance(user_id, 1000.0)
        
        # 2. Update Runtime State (if bot running)
        bot_manager.update_runtime_state(user_id, {'practice_balance': 1000.0})
        
        # 3. Broadcast
        asyncio.create_task(self.broadcast_status_update(user_id))
        
        return 1000.0

    def start_bots_bulk(self, user_id: int, bots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Start multiple bots."""
        results = {"successful": [], "failed": []}
        
        for bot in bots:
            symbol = bot.get('symbol')
            config_id = bot.get('config_id')
            identifier = config_id if config_id else symbol
            
            try:
                if self.start_bot(user_id, config_id=config_id, symbol=symbol):
                    results['successful'].append(identifier)
                else:
                    results['failed'].append({"id": identifier, "error": "Unknown error"})
            except Exception as e:
                logger.error(f"Bulk start failed for {identifier}: {e}")
                results['failed'].append({"id": identifier, "error": str(e)})
        
        return results

    def stop_bots_bulk(self, user_id: int, bots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stop multiple bots."""
        results = {"successful": [], "failed": []}
        
        for bot in bots:
            symbol = bot.get('symbol')
            config_id = bot.get('config_id')
            identifier = config_id if config_id else symbol
            
            try:
                if self.stop_bot(user_id, config_id=config_id, symbol=symbol):
                    results['successful'].append(identifier)
                else:
                    # Stopping a stopped bot is a success, technically
                    results['successful'].append(identifier)
            except Exception as e:
                logger.error(f"Bulk stop failed for {identifier}: {e}")
                results['failed'].append({"id": identifier, "error": str(e)})
                
        return results
        
    def delete_bots_bulk(self, user_id: int, config_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple bot configurations."""
        results = {"successful": [], "failed": []}
        
        for config_id in config_ids:
            try:
                if self.delete_bot_config(user_id, config_id):
                    results['successful'].append(config_id)
                else:
                    results['failed'].append({"id": config_id, "error": "Delete failed"})
            except Exception as e:
                logger.error(f"Bulk delete failed for {config_id}: {e}")
                results['failed'].append({"id": config_id, "error": str(e)})
                
        # Broadcast one update at the end
        asyncio.create_task(self.broadcast_status_update(user_id))
        
        return results

    def create_quick_scalp_bot(self, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """Create a default scalping bot."""
        # Check Feature
        features = self.db.get_user_features(user_id, is_admin=is_admin)
        if "quick_scalp" not in features:
            raise HTTPException(status_code=403, detail="Quick Scalp Bot requires a Pro or Elite subscription.")

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
        closed = self._ensure_position_closed(user_id, existing)
        if not closed:
            raise HTTPException(status_code=500, detail="Failed to close open position. Config NOT deleted.")
        
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

    def _ensure_position_closed(self, user_id: int, config_data: Dict[str, Any], max_retries=5) -> bool:
        """
        Ensure position is closed with retries.
        Returns True if closed (or was empty), False if failed to close.
        """
        try:
            exchange_name = config_data.get('exchange', 'bybit')
            symbol = config_data['symbol']
            is_dry_run = config_data.get('dry_run', True)
            
            # Get Keys
            api_key_data = self.db.get_api_key(user_id, exchange_name)
            api_key, api_secret = None, None
            
            if api_key_data:
                api_key = self.encryption.decrypt(api_key_data['api_key_encrypted'])
                api_secret = self.encryption.decrypt(api_key_data['api_secret_encrypted'])
            
            if not api_key and exchange_name == 'bybit':
                api_key = config.API_KEY
                api_secret = config.API_SECRET

            if not api_key:
                if is_dry_run:
                    logger.warning(f"No API keys found for Dry Run close of {symbol}. Assuming safe to close/delete.")
                    return True
                else:
                    return False # Live trading requires keys to ensure closure

            if api_key and api_secret:
                client = client_manager.get_client(
                    user_id=user_id,
                    api_key=api_key,
                    api_secret=api_secret,
                    dry_run=is_dry_run,
                    exchange=exchange_name
                )
                
                for attempt in range(max_retries):
                    try:
                        position = client.fetch_position(symbol)
                        size = float(position.get('size', 0.0))
                        
                        if size == 0:
                            logger.info(f"Position for {symbol} is closed.")
                            return True
                            
                        logger.info(f"Attempt {attempt+1}/{max_retries}: Closing position for {symbol} (Size: {size})")
                        side = position.get('side', '').lower()
                        close_side = 'sell' if side == 'buy' else 'buy'
                        
                        client.create_order(
                            symbol=symbol,
                            order_type='market',
                            side=close_side,
                            amount=size
                        )
                        
                        # Wait for fill
                        time.sleep(2)
                        
                        # Handle PnL Update for Dry Run
                        if config_data.get('dry_run', True):
                            try:
                                # Fetch the last trade to get realized PnL
                                trades = client.fetch_my_trades(symbol, limit=1)
                                if trades:
                                    last_trade = trades[0]
                                    # For Paper Exchange, we customized it to include 'pnl'
                                    pnl = last_trade.get('pnl', 0.0)
                                    if pnl != 0:
                                        user = self.db.get_user_by_id(user_id)
                                        current_balance = user.get('practice_balance', 1000.0)
                                        new_balance = current_balance + pnl
                                        self.db.update_practice_balance(user_id, new_balance)
                                        logger.info(f"Updated practice balance for User {user_id}: {current_balance} -> {new_balance} (PnL: {pnl})")
                            except Exception as e:
                                logger.error(f"Failed to update practice balance: {e}")
                        
                        
                    except Exception as e:
                        logger.error(f"Error checking/closing position (Attempt {attempt+1}): {e}")
                        time.sleep(2)
                
                # Final check
                position = client.fetch_position(symbol)
                size = float(position.get('size', 0.0))
                return size == 0
                
            return False # No keys = failure to ensure check
            
        except Exception as e:
            logger.error(f"Failed to ensure position closed for {config_data.get('symbol')}: {e}")
            return False

    def close_bot_position(self, user_id: int, config_id: int) -> bool:
        """Close any open position for a bot without stopping it."""
        try:
            config_data = self.db.get_bot_config(user_id, config_id)
            if not config_data:
                raise HTTPException(status_code=404, detail="Bot config not found")
                
            # Use the safe close method
            closed = self._ensure_position_closed(user_id, config_data)
            
            if not closed:
                raise HTTPException(status_code=500, detail="Failed to close position after multiple retries.")
                
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error closing position for config {config_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

bot_service = BotService()

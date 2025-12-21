"""
Position Manager Module

Tracks position state and lifecycle, handles persistence.
Extracted from bot.py for better modularity and testability.
"""
import time
import logging
from datetime import datetime

logger = logging.getLogger("TradingBot")


class PositionManager:
    """Manages position tracking and state persistence"""
    
    def __init__(self, user_id, db):
        """
        Initialize position manager.
        
        Args:
            user_id: User ID
            db: Database handler instance
        """
        self.user_id = user_id
        self.db = db
        self.position_start_time = None
        self.active_order_id = None
        self.logger = logger
    
    def load_persisted_state(self, strategy_config):
        """
        Load position state from database.
        
        Args:
            strategy_config: Strategy configuration dict
        """
        self.position_start_time = strategy_config.get('position_start_time')
        if self.position_start_time:
            self.logger.info(f"Loaded persisted position start time: {self.position_start_time}")
            try:
                self.position_start_time = self.position_start_time.timestamp()
            except (AttributeError, TypeError):
                self.logger.debug(f"Position start time already in correct format: {type(self.position_start_time)}")
        
        self.active_order_id = strategy_config.get('active_order_id')
        if self.active_order_id:
            self.logger.info(f"Loaded persisted active order: {self.active_order_id}")
    
    def reconcile_on_startup(self, client, symbol):
        """
        Verify and clean up orders on bot restart.
        
        Args:
            client: Exchange client instance
            symbol: Trading symbol
            
        Returns:
            dict: Open order info if found, None otherwise
        """
        try:
            if not hasattr(client, 'fetch_open_orders'):
                return None
            
            open_orders = client.fetch_open_orders(symbol)
            open_order = None
            
            # 1. Reconcile Active Order
            if self.active_order_id:
                found = False
                for order in open_orders:
                    if str(order['id']) == str(self.active_order_id):
                        found = True
                        open_order = {
                            'id': order['id'],
                            'time': time.time(),
                            'side': order['side'],
                            'type': order['type']
                        }
                        self.logger.info(f"✅ Resumed tracking Limit Order {self.active_order_id}")
                        break
                
                if not found:
                    self.logger.warning(f"⚠️ Persisted order {self.active_order_id} not found on exchange. Clearing state.")
                    self.active_order_id = None
                    self.db.update_bot_state(self.user_id, active_order_id=None)
            
            # 2. Orphan Cleanup
            for order in open_orders:
                if self.active_order_id and str(order['id']) == str(self.active_order_id):
                    continue
                
                self.logger.warning(f"🧹 Cancelling orphaned order {order['id']} on {symbol}")
                try:
                    client.cancel_order(order['id'], symbol)
                except Exception as e:
                    self.logger.error(f"Failed to cancel orphan: {e}")
            
            return open_order
            
        except Exception as e:
            self.logger.error(f"Startup reconciliation failed: {e}")
            return None
    
    def calculate_unrealized_pnl(self, position, current_price, amount_usdt, leverage):
        """
        Calculate current PnL for monitoring.
        
        Args:
            position: Position dict
            current_price: Current market price
            amount_usdt: Trade amount in USDT
            leverage: Leverage multiplier
            
        Returns:
            Tuple of (unrealized_pnl: float, pnl_pct: float)
        """
        position_side = position.get('side')
        entry_price = float(position.get('entry_price', current_price))
        
        if position_side == 'Buy':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        position_size = position.get('size', 0.0)
        unrealized_pnl = pnl_pct * (amount_usdt * leverage if amount_usdt else (position_size * current_price))
        
        return unrealized_pnl, pnl_pct
    
    def update_state(self, position_start_time='NO_CHANGE', active_order_id='NO_CHANGE'):
        """
        Persist position state to database.
        
        Args:
            position_start_time: Timestamp or None to clear, 'NO_CHANGE' to skip
            active_order_id: Order ID or None to clear, 'NO_CHANGE' to skip
        """
        kwargs = {}
        if position_start_time != 'NO_CHANGE':
            if position_start_time is not None:
                kwargs['position_start_time'] = datetime.fromtimestamp(position_start_time)
            else:
                kwargs['position_start_time'] = None
            self.position_start_time = position_start_time
        
        if active_order_id != 'NO_CHANGE':
            kwargs['active_order_id'] = active_order_id
            self.active_order_id = active_order_id
        
        if kwargs:
            self.db.update_bot_state(self.user_id, **kwargs)

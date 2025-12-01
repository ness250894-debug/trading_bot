import threading
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger("BotManager")

class BotInstance:
    """Represents a single user's bot instance."""
    
    def __init__(self, user_id: int, strategy_config: dict):
        self.user_id = user_id
        self.strategy_config = strategy_config
        self.thread: Optional[threading.Thread] = None
        self.running_event = threading.Event()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        # Runtime state for dynamic metrics (like active trades)
        self.runtime_state: Dict[str, Any] = {"active_trades": 0}
    
    def is_running(self) -> bool:
        """Check if bot instance is currently running."""
        return self.running_event.is_set() and self.thread and self.thread.is_alive()
    
    def get_status(self) -> dict:
        """Get current status of this bot instance."""
        return {
            "user_id": self.user_id,
            "is_running": self.is_running(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "strategy": self.strategy_config.get("STRATEGY", "unknown"),
            "symbol": self.strategy_config.get("SYMBOL", "unknown"),
            "active_trades": self.runtime_state.get("active_trades", 0)
        }


class BotManager:
    """Manages multiple bot instances (one per user)."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BotManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Changed: Support multiple instances per user (one per symbol)
        # instances[user_id][symbol] = BotInstance
        self.instances: Dict[int, Dict[str, BotInstance]] = {}
        self.instances_lock = threading.Lock()
        self._initialized = True
        logger.info("BotManager initialized with multi-instance support")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of BotManager."""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def start_bot(self, user_id: int, strategy_config: dict, symbol: str = None) -> bool:
        """
        Start a bot instance for a user and symbol.
        
        Args:
            user_id: User ID
            strategy_config: Strategy configuration dict
            symbol: Trading symbol (e.g., 'BTC/USDT'). If None, uses config['SYMBOL']
        
        Returns:
            True if successful
        """
        # Extract symbol from config if not provided
        if symbol is None:
            symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
        
        with self.instances_lock:
            # Initialize user's instances dict if needed
            if user_id not in self.instances:
                self.instances[user_id] = {}
            
            # Stop existing instance for this symbol if running
            if symbol in self.instances[user_id]:
                logger.info(f"Stopping existing bot for user {user_id}, symbol {symbol}")
                self._stop_bot_internal(user_id, symbol)
            
            # Create new instance
            instance = BotInstance(user_id, strategy_config)
            
            # Import here to avoid circular dependency
            from .bot import run_bot_instance
            
            # Start bot in separate thread
            def bot_thread_wrapper():
                try:
                    instance.started_at = datetime.now()
                    instance.running_event.set()
                    # Pass runtime_state to the bot loop
                    run_bot_instance(user_id, strategy_config, instance.running_event, instance.runtime_state)
                except Exception as e:
                    logger.error(f"Bot instance for user {user_id}, symbol {symbol} crashed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    instance.stopped_at = datetime.now()
                    instance.running_event.clear()
            
            instance.thread = threading.Thread(
                target=bot_thread_wrapper,
                name=f"Bot-User-{user_id}-{symbol.replace('/', '-')}",
                daemon=True
            )
            instance.thread.start()
            
            self.instances[user_id][symbol] = instance
            logger.info(f"Started bot instance for user {user_id}, symbol {symbol}")
            return True
    
    
    def _stop_bot_internal(self, user_id: int, symbol: str) -> bool:
        """Internal method to stop a specific bot instance (must be called with lock held)."""
        if user_id not in self.instances or symbol not in self.instances[user_id]:
            return False
        
        instance = self.instances[user_id][symbol]
        
        if not instance.is_running():
            logger.info(f"Bot instance for user {user_id}, symbol {symbol} already stopped")
            # Clean up non-running instance
            del self.instances[user_id][symbol]
            if not self.instances[user_id]:
                del self.instances[user_id]
            return True
        
        # Signal bot to stop
        instance.running_event.clear()
        instance.stopped_at = datetime.now()
        
        # Wait for thread to finish (with timeout)
        if instance.thread:
            instance.thread.join(timeout=5.0)
        
        # Remove instance
        del self.instances[user_id][symbol]
        
        # Clean up user entry if no instances left
        if not self.instances[user_id]:
            del self.instances[user_id]
        
        logger.info(f"Stopped bot instance for user {user_id}, symbol {symbol}")
        return True
    
    def stop_bot(self, user_id: int, symbol: str = None) -> bool:
        """
        Stop a bot instance for a user and symbol.
        
        Args:
            user_id: User ID
            symbol: Trading symbol. If None, stops ALL instances for this user
        
        Returns:
            True if successful
        """
        with self.instances_lock:
            if user_id not in self.instances:
                logger.warning(f"No bot instances found for user {user_id}")
                return False
            
            # If symbol not specified, stop all instances for user
            if symbol is None:
                symbols_to_stop = list(self.instances[user_id].keys())
                logger.info(f"Stopping all {len(symbols_to_stop)} bot instances for user {user_id}")
                for sym in symbols_to_stop:
                    self._stop_bot_internal(user_id, sym)
                return True
            
            # Stop specific symbol
            if symbol not in self.instances[user_id]:
                logger.warning(f"No bot instance found for user {user_id}, symbol {symbol}")
                return False
            
            return self._stop_bot_internal(user_id, symbol)
    
    
    def restart_bot(self, user_id: int, strategy_config: dict, symbol: str = None) -> bool:
        """
        Restart a bot instance with new configuration.
        
        Args:
            user_id: User ID
            strategy_config: New strategy configuration
            symbol: Trading symbol. If None, uses config['SYMBOL']
        """
        if symbol is None:
            symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
        
        logger.info(f"Restarting bot for user {user_id}, symbol {symbol}")
        self.stop_bot(user_id, symbol)
        return self.start_bot(user_id, strategy_config, symbol)
    
    
    def get_status(self, user_id: int, symbol: str = None) -> Optional[dict]:
        """
        Get status of a specific user's bot instance(s).
        
        Args:
            user_id: User ID
            symbol: Trading symbol. If None, returns status for all symbols
        
        Returns:
            Dict with status, or None if no instances found
        """
        with self.instances_lock:
            if user_id not in self.instances:
                return None
            
            # If symbol specified, return status for that symbol only
            if symbol is not None:
                if symbol not in self.instances[user_id]:
                    return None
                return self.instances[user_id][symbol].get_status()
            
            # Return status for all symbols
            return {
                sym: instance.get_status()
                for sym, instance in self.instances[user_id].items()
            }
    
    
    def get_all_running(self) -> list:
        """Get all currently running bot instances (admin function)."""
        with self.instances_lock:
            all_instances = []
            for user_id, user_instances in self.instances.items():
                for symbol, instance in user_instances.items():
                    if instance.is_running():
                        all_instances.append(instance.get_status())
            return all_instances
    
    
    def get_running_event(self, user_id: int, symbol: str = None) -> Optional[threading.Event]:
        """
        Get the running event for a user's bot (for pause/resume).
        
        Args:
            user_id: User ID
            symbol: Trading symbol. If None and user has only one instance, returns that.
                   If None and user has multiple instances, returns None.
        """
        with self.instances_lock:
            if user_id not in self.instances:
                return None
            
            # If symbol specified, return event for that symbol
            if symbol is not None:
                if symbol in self.instances[user_id]:
                    return self.instances[user_id][symbol].running_event
                return None
            
            # If only one instance, return it
            if len(self.instances[user_id]) == 1:
                return list(self.instances[user_id].values())[0].running_event
            
            # Multiple instances, symbol required
            return None


# Global singleton instance
bot_manager = BotManager.get_instance()

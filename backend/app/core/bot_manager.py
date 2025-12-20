import threading
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger("BotManager")

class LogCaptureHandler(logging.Handler):
    """Intercepts logs and routes them to the correct BotInstance based on thread name."""
    def emit(self, record):
        try:
            msg = self.format(record)
            thread_name = record.threadName
            # Format: "Bot-User-{user_id}-Config-{config_id}"
            if "Bot-User-" in thread_name:
                parts = thread_name.split("-")
                # Expected: ['Bot', 'User', '1', 'Config', '123'] (len=5)
                if len(parts) >= 5:
                    # user_id = int(parts[2])
                    config_id = int(parts[4])
                    # We need access to bot_manager instance to find the bot
                    # We need access to bot_manager instance to find the bot
                    # Since this is a class, we can access the singleton via global or class method
                    manager = BotManager.get_instance()
                    # We need to find the user_id context efficiently or iterate
                    # Since we have config_id and user_id in thread name, we can lookup directly
                    user_id = int(parts[2])
                    
                    if user_id in manager.instances and config_id in manager.instances[user_id]:
                        bot_instance = manager.instances[user_id][config_id]
                        bot_instance.logs.append(msg)
        except Exception:
            self.handleError(record)

class BotInstance:
    """Represents a single user's bot instance."""
    
    def __init__(self, user_id: int, config_id: int, strategy_config: dict):
        self.user_id = user_id
        self.config_id = config_id
        self.strategy_config = strategy_config
        self.thread: Optional[threading.Thread] = None
        self.running_event = threading.Event()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        # Runtime state for dynamic metrics (like active trades)
        self.runtime_state: Dict[str, Any] = {"active_trades": 0}
        # Log buffer
        self.logs = deque(maxlen=50)
    
    def is_running(self) -> bool:
        """Check if bot instance is currently running."""
        return self.running_event.is_set() and self.thread and self.thread.is_alive()
    
    def get_status(self) -> dict:
        """Get current status of this bot instance."""
        return {
            "user_id": self.user_id,
            "config_id": self.config_id,
            "is_running": self.is_running(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "strategy": self.strategy_config.get("STRATEGY", "unknown"),
            "symbol": self.strategy_config.get("SYMBOL", "unknown"),
            "active_trades": self.runtime_state.get("active_trades", 0),
            "pnl": self.runtime_state.get("pnl", 0.0),
            "roi": self.runtime_state.get("roi", 0.0),
            "current_price": self.runtime_state.get("current_price", 0.0),
            "tp_price": self.runtime_state.get("tp_price", 0.0),
            "sl_price": self.runtime_state.get("sl_price", 0.0),
            "logs": list(self.logs)
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
        
        # Changed: Support multiple instances per user (keyed by config_id)
        # instances[user_id][config_id] = BotInstance
        self.instances: Dict[int, Dict[int, BotInstance]] = {}
        self.instances_lock = threading.Lock()
        self._initialized = True
        self.instances: Dict[int, Dict[int, BotInstance]] = {}
        self.instances_lock = threading.Lock()
        self._initialized = True
        
        # Attach Log Capture Handler
        capture_handler = LogCaptureHandler()
        capture_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        capture_handler.setFormatter(formatter)
        
        # Attach to the TradingBot logger (defined in bot.py)
        # We need to ensure bot.py imports don't cycle, but getting logger by name is safe
        bot_logger = logging.getLogger("TradingBot")
        bot_logger.addHandler(capture_handler)
        
        logger.info("BotManager initialized with multi-instance support and LogCapture")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of BotManager."""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def start_bot(self, user_id: int, strategy_config: dict, config_id: int = None, main_loop = None) -> bool:
        """
        Start a bot instance for a user and config.
        
        Args:
            user_id: User ID
            strategy_config: Strategy configuration dict
            config_id: Configuration ID. If None, assumes legacy single-bot mode (use 0)
            main_loop: Main thread asyncio loop (optional, but needed for WebSocket events)
        
        Returns:
            True if successful
        """
        # If config_id not provided, use 0 (legacy/default)
        if config_id is None:
            config_id = 0
            
        symbol = strategy_config.get('SYMBOL', 'BTC/USDT')
        
        with self.instances_lock:
            # Initialize user's instances dict if needed
            if user_id not in self.instances:
                self.instances[user_id] = {}
            
            # Stop existing instance for this config if running
            if config_id in self.instances[user_id]:
                logger.info(f"Stopping existing bot for user {user_id}, config {config_id}")
                self._stop_bot_internal(user_id, config_id)
            
            # Create new instance
            instance = BotInstance(user_id, config_id, strategy_config)
            
            # Import here to avoid circular dependency
            from .bot import run_bot_instance
            
            # Start bot in separate thread
            def bot_thread_wrapper():
                try:
                    instance.started_at = datetime.now()
                    instance.running_event.set()
                    # Pass runtime_state and main_loop to the bot loop
                    run_bot_instance(user_id, strategy_config, instance.running_event, instance.runtime_state, main_loop)
                except Exception as e:
                    logger.error(f"Bot instance for user {user_id}, config {config_id} crashed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    instance.stopped_at = datetime.now()
                    instance.running_event.clear()
            
            instance.thread = threading.Thread(
                target=bot_thread_wrapper,
                name=f"Bot-User-{user_id}-Config-{config_id}",
                daemon=True
            )
            instance.thread.start()
            
            self.instances[user_id][config_id] = instance
            logger.info(f"Started bot instance for user {user_id}, config {config_id} ({symbol})")
            
            # Start Notification Scheduler for this user
            from .notification_scheduler import start_scheduler
            start_scheduler(user_id)
            
            return True
    
    
    def _stop_bot_internal(self, user_id: int, config_id: int) -> bool:
        """Internal method to stop a specific bot instance (must be called with lock held)."""
        if user_id not in self.instances or config_id not in self.instances[user_id]:
            return False
        
        instance = self.instances[user_id][config_id]
        
        if not instance.is_running():
            logger.info(f"Bot instance for user {user_id}, config {config_id} already stopped")
            # Clean up non-running instance
            del self.instances[user_id][config_id]
            if not self.instances[user_id]:
                del self.instances[user_id]
                from .notification_scheduler import stop_scheduler
                stop_scheduler(user_id)
            return True
        
        # Signal bot to stop
        instance.running_event.clear()
        instance.stopped_at = datetime.now()
        
        # Wait for thread to finish (with timeout)
        if instance.thread:
            instance.thread.join(timeout=5.0)
        
        # Remove instance
        del self.instances[user_id][config_id]
        
        # Clean up user entry if no instances left
        if not self.instances[user_id]:
            del self.instances[user_id]
            from .notification_scheduler import stop_scheduler
            stop_scheduler(user_id)
        
        logger.info(f"Stopped bot instance for user {user_id}, config {config_id}")
        return True
    
    def stop_bot(self, user_id: int, config_id: int = None, symbol: str = None) -> bool:
        """
        Stop a bot instance for a user.
        
        Args:
            user_id: User ID
            config_id: Configuration ID. If None, checks symbol.
            symbol: Trading symbol (Legacy support). If provided and config_id is None, stops all bots with this symbol.
                    If both None, stops ALL instances for this user.
        
        Returns:
            True if successful
        """
        with self.instances_lock:
            if user_id not in self.instances:
                logger.warning(f"No bot instances found for user {user_id}")
                return False
            
            # If config_id specified, stop that specific bot
            if config_id is not None:
                if config_id not in self.instances[user_id]:
                    logger.warning(f"No bot instance found for user {user_id}, config {config_id}")
                    return False
                return self._stop_bot_internal(user_id, config_id)
            
            # If symbol specified (legacy support), stop all bots with that symbol
            if symbol is not None:
                stopped_any = False
                # Create list to avoid runtime error during iteration
                configs_to_check = list(self.instances[user_id].items())
                for cid, instance in configs_to_check:
                    if instance.strategy_config.get('SYMBOL') == symbol:
                        if self._stop_bot_internal(user_id, cid):
                            stopped_any = True
                return stopped_any
            
            # If neither specified, stop all instances for user
            configs_to_stop = list(self.instances[user_id].keys())
            logger.info(f"Stopping all {len(configs_to_stop)} bot instances for user {user_id}")
            for cid in configs_to_stop:
                self._stop_bot_internal(user_id, cid)
            return True
    
    
    def restart_bot(self, user_id: int, strategy_config: dict, config_id: int = None, symbol: str = None) -> bool:
        """
        Restart a bot instance with new configuration.
        """
        if config_id is None:
            config_id = 0
            
        logger.info(f"Restarting bot for user {user_id}, config {config_id}")
        self.stop_bot(user_id, config_id=config_id)
        return self.start_bot(user_id, strategy_config, config_id=config_id)
    
    
    def get_status(self, user_id: int, config_id: int = None, symbol: str = None) -> Optional[dict]:
        """
        Get status of a specific user's bot instance(s).
        
        Args:
            user_id: User ID
            config_id: Config ID. If provided, returns status for that bot.
            symbol: Symbol (Legacy). If provided, returns status for all bots with that symbol.
        
        Returns:
            Dict with status, or None if no instances found
        """
        with self.instances_lock:
            if user_id not in self.instances:
                return None
            
            # If config_id specified, return status for that config
            if config_id is not None:
                if config_id not in self.instances[user_id]:
                    return None
                return self.instances[user_id][config_id].get_status()
            
            # If symbol specified, return dict of statuses for that symbol
            if symbol is not None:
                statuses = {}
                for cid, instance in self.instances[user_id].items():
                    if instance.strategy_config.get('SYMBOL') == symbol:
                        statuses[cid] = instance.get_status()
                return statuses if statuses else None
            
            # Return status for all instances (keyed by config_id)
            return {
                cid: instance.get_status()
                for cid, instance in self.instances[user_id].items()
            }
    
    
    def get_all_running(self) -> list:
        """Get all currently running bot instances (admin function)."""
        with self.instances_lock:
            all_instances = []
            for user_id, user_instances in self.instances.items():
                for config_id, instance in user_instances.items():
                    if instance.is_running():
                        all_instances.append(instance.get_status())
            return all_instances
    
    
    def get_running_event(self, user_id: int, config_id: int = None) -> Optional[threading.Event]:
        """
        Get the running event for a user's bot (for pause/resume).
        """
        with self.instances_lock:
            if user_id not in self.instances:
                return None
            
            # If config_id specified, return event for that config
            if config_id is not None:
                if config_id in self.instances[user_id]:
                    return self.instances[user_id][config_id].running_event
                return None
            
            # If only one instance, return it
            if len(self.instances[user_id]) == 1:
                return list(self.instances[user_id].values())[0].running_event
            
            return None


# Global singleton instance
bot_manager = BotManager.get_instance()

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
        
        self.instances: Dict[int, BotInstance] = {}
        self.instances_lock = threading.Lock()
        self._initialized = True
        logger.info("BotManager initialized")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of BotManager."""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def start_bot(self, user_id: int, strategy_config: dict) -> bool:
        """Start a bot instance for a user."""
        with self.instances_lock:
            # Stop existing instance if running
            if user_id in self.instances:
                self.stop_bot(user_id)
            
            # Create new instance
            instance = BotInstance(user_id, strategy_config)
            
            # Import here to avoid circular dependency
            from .bot import run_bot_instance
            
            # Start bot in separate thread
            def bot_thread_wrapper():
                try:
                    instance.started_at = datetime.now()
                    instance.running_event.set()
                    run_bot_instance(user_id, strategy_config, instance.running_event)
                except Exception as e:
                    logger.error(f"Bot instance for user {user_id} crashed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    instance.stopped_at = datetime.now()
                    instance.running_event.clear()
            
            instance.thread = threading.Thread(
                target=bot_thread_wrapper,
                name=f"Bot-User-{user_id}",
                daemon=True
            )
            instance.thread.start()
            
            self.instances[user_id] = instance
            logger.info(f"Started bot instance for user {user_id}")
            return True
    
    def stop_bot(self, user_id: int) -> bool:
        """Stop a bot instance for a user."""
        with self.instances_lock:
            if user_id not in self.instances:
                logger.warning(f"No bot instance found for user {user_id}")
                return False
            
            instance = self.instances[user_id]
            
            if not instance.is_running():
                logger.info(f"Bot instance for user {user_id} already stopped")
                return True
            
            # Signal bot to stop
            instance.running_event.clear()
            instance.stopped_at = datetime.now()
            
            # Wait for thread to finish (with timeout)
            if instance.thread:
                instance.thread.join(timeout=5.0)
            
            logger.info(f"Stopped bot instance for user {user_id}")
            return True
    
    def restart_bot(self, user_id: int, strategy_config: dict) -> bool:
        """Restart a bot instance with new configuration."""
        logger.info(f"Restarting bot for user {user_id}")
        self.stop_bot(user_id)
        return self.start_bot(user_id, strategy_config)
    
    def get_status(self, user_id: int) -> Optional[dict]:
        """Get status of a specific user's bot instance."""
        with self.instances_lock:
            if user_id not in self.instances:
                return None
            return self.instances[user_id].get_status()
    
    def get_all_running(self) -> list:
        """Get all currently running bot instances (admin function)."""
        with self.instances_lock:
            return [
                instance.get_status()
                for instance in self.instances.values()
                if instance.is_running()
            ]
    
    def get_running_event(self, user_id: int) -> Optional[threading.Event]:
        """Get the running event for a user's bot (for pause/resume)."""
        with self.instances_lock:
            if user_id in self.instances:
                return self.instances[user_id].running_event
            return None


# Global singleton instance
bot_manager = BotManager.get_instance()

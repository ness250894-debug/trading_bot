"""
Exchange client manager with connection pooling and caching.
Prevents creating new client instances on every API request.
"""
import logging
from typing import Dict, Optional
import threading
from ..core import config

logger = logging.getLogger("ClientManager")

class ClientManager:
    """Manages exchange client instances with caching."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ClientManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._clients: Dict[str, any] = {}  # key: user_id or 'global'
        self._clients_lock = threading.Lock()
        self._initialized = True
        logger.info("ClientManager initialized")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def get_client(self, user_id: Optional[int] = None, api_key: str = None, api_secret: str = None, dry_run: bool = False, exchange: str = 'bybit'):
        """
        Get or create exchange client.
        
        Args:
            user_id: User ID for per-user caching
            api_key: API key (if not provided, uses global config)
            api_secret: API secret
            dry_run: Whether to use paper trading
            exchange: Exchange name ('bybit', 'binance', etc.)
        """
        cache_key = f"user_{user_id}_{exchange}" if user_id else f"global_{exchange}"
        
        with self._clients_lock:
            # Return cached client if exists
            if cache_key in self._clients:
                return self._clients[cache_key]
            
            # Create new client
            if api_key is None:
                api_key = config.API_KEY
            if api_secret is None:
                api_secret = config.API_SECRET
            
            if dry_run:
                from .exchange.paper import PaperExchange
                client = PaperExchange(api_key, api_secret, exchange_type=exchange)
            else:
                from .exchange.exchange_factory import ExchangeFactory
                # Validate exchange is supported
                if not ExchangeFactory.is_supported(exchange):
                    logger.error(f"Exchange '{exchange}' is not supported")
                    raise ValueError(f"Exchange '{exchange}' is not supported. Supported: {ExchangeFactory.get_supported_exchanges()}")
                
                client = ExchangeFactory.create_exchange(
                    exchange, api_key, api_secret, demo=config.DEMO, timeout=10000
                )
            
            # Cache client
            self._clients[cache_key] = client
            logger.info(f"Created and cached {exchange} client for {cache_key}")
            
            return client
    
    def clear_cache(self, user_id: Optional[int] = None, exchange: Optional[str] = None):
        """Clear cached client (useful when API keys change)."""
        if user_id and exchange:
            cache_key = f"user_{user_id}_{exchange}"
        elif user_id:
            # Clear all exchanges for this user
            cache_key = f"user_{user_id}"
        elif exchange:
            cache_key = f"global_{exchange}"
        else:
            cache_key = "global"
        
        with self._clients_lock:
            # Clear specific key or all matching keys
            if cache_key in self._clients:
                del self._clients[cache_key]
                logger.info(f"Cleared client cache for {cache_key}")
            else:
                # Clear all keys matching pattern
                keys_to_clear = [k for k in self._clients.keys() if k.startswith(cache_key)]
                for k in keys_to_clear:
                    del self._clients[k]
                if keys_to_clear:
                    logger.info(f"Cleared {len(keys_to_clear)} client cache entries for {cache_key}")


# Global instance
client_manager = ClientManager.get_instance()

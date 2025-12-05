"""
Exchange Factory for creating exchange client instances.
Supports: ByBit, Binance, Kraken, OKX, Coinbase
"""
from typing import Dict, Type, List
from .base_client import BaseExchangeClient
from .client import ByBitClient
from .binance_client import BinanceClient
from .kraken_client import KrakenClient
from .okx_client import OKXClient
from .coinbase_client import CoinbaseClient


class ExchangeFactory:
    """Factory for creating exchange client instances."""
    
    # Registry of supported exchanges
    _registry: Dict[str, Type[BaseExchangeClient]] = {
        'bybit': ByBitClient,
        'binance': BinanceClient,
        'kraken': KrakenClient,
        'okx': OKXClient,
        'coinbase': CoinbaseClient,
    }
    
    @classmethod
    def create_exchange(
        cls, 
        exchange_name: str, 
        api_key: str, 
        api_secret: str, 
        demo: bool = True,
        timeout: int = 10000
    ) -> BaseExchangeClient:
        """
        Create an exchange client instance.
        
        Args:
            exchange_name: Name of the exchange ('bybit', 'binance', etc.)
            api_key: API key
            api_secret: API secret
            demo: Whether to use demo/testnet mode
            timeout: Request timeout in milliseconds
            
        Returns:
            Exchange client instance
            
        Raises:
            ValueError: If exchange is not supported
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in cls._registry:
            raise ValueError(
                f"Exchange '{exchange_name}' is not supported. "
                f"Supported exchanges: {', '.join(cls.get_supported_exchanges())}"
            )
        
        exchange_class = cls._registry[exchange_name]
        return exchange_class(api_key, api_secret, demo=demo, timeout=timeout)
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """
        Get list of supported exchange names.
        
        Returns:
            List of exchange names
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_supported(cls, exchange_name: str) -> bool:
        """
        Check if an exchange is supported.
        
        Args:
            exchange_name: Name of the exchange
            
        Returns:
            True if supported, False otherwise
        """
        return exchange_name.lower() in cls._registry
    
    @classmethod
    def get_exchange_info(cls) -> List[Dict[str, any]]:
        """
        Get information about all supported exchanges.
        
        Returns:
            List of dictionaries with exchange information
        """
        # Display names for exchanges
        display_names = {
            'bybit': 'ByBit',
            'binance': 'Binance',
            'kraken': 'Kraken',
            'okx': 'OKX',
            'coinbase': 'Coinbase',
        }
        
        info = []
        for exchange_name in cls._registry.keys():
            info.append({
                'name': exchange_name,
                'display_name': display_names.get(exchange_name, exchange_name.capitalize()),
                'supports_demo': True,
                'supports_futures': exchange_name in ['bybit', 'binance', 'okx'],
                'supports_spot': True,
            })
        return info


# Backward compatibility: Export ByBitClient as ExchangeClient
# This allows existing code to continue working without changes
ExchangeClient = ByBitClient

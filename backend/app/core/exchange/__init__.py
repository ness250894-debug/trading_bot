"""
Exchange module exports.
Provides backward compatibility while enabling new multi-exchange architecture.
"""
from .base_client import BaseExchangeClient
from .client import ByBitClient
from .binance_client import BinanceClient
from .kraken_client import KrakenClient
from .okx_client import OKXClient
from .coinbase_client import CoinbaseClient
from .exchange_factory import ExchangeFactory, ExchangeClient
from .paper import PaperExchange

__all__ = [
    'BaseExchangeClient',
    'ByBitClient',
    'BinanceClient',
    'KrakenClient',
    'OKXClient',
    'CoinbaseClient',
    'ExchangeClient',  # Backward compatibility alias
    'ExchangeFactory',
    'PaperExchange',
]

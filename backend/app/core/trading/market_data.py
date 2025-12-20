"""
Market Data Fetcher Module

Centralizes all market data fetching logic with retry mechanisms.
Extracted from bot.py for better modularity and testability.
"""
import logging
from ..resilience import retry

logger = logging.getLogger("TradingBot")


class MarketDataFetcher:
    """Handles fetching market data and positions with retry logic"""
    
    def __init__(self, client, symbol, timeframe):
        """
        Initialize market data fetcher.
        
        Args:
            client: Exchange client instance
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1m', '1h')
        """
        self.client = client
        self.symbol = symbol
        self.timeframe = timeframe
        self.logger = logger
    
    @retry(max_attempts=3, delay=1, backoff=2)
    def fetch_ohlcv(self, limit=100):
        """
        Fetch OHLCV data with retry logic.
        
        Args:
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.client.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
    
    @retry(max_attempts=3, delay=1, backoff=2)
    def fetch_position(self):
        """
        Fetch current position with retry logic.
        
        Returns:
            Position dictionary
        """
        return self.client.fetch_position(self.symbol)
    
    def get_current_price(self, df):
        """
        Extract current price from latest candle.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Current close price
        """
        return df['close'].iloc[-1]

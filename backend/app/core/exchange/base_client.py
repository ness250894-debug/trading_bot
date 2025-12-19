from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Optional, Dict, Any, List


class BaseExchangeClient(ABC):
    """
    Abstract base class for exchange clients.
    All exchange implementations must extend this class and implement all abstract methods.
    """
    
    def __init__(self, api_key: str, api_secret: str, timeout: int = 10000):
        """
        Initialize base exchange client.
        
        Args:
            api_key: API key for the exchange
            api_secret: API secret for the exchange
            timeout: Request timeout in milliseconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange = None  # To be set by subclass
        
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100, since: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch OHLCV (candlestick) data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            limit: Number of candles to fetch
            since: Timestamp in milliseconds to fetch from
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def fetch_balance(self) -> Dict[str, Any]:
        """
        Fetch account balance.
        
        Returns:
            Dictionary with structure:
            {
                'total': {'USDT': 1000.0, ...},
                'free': {'USDT': 500.0, ...},
                'used': {'USDT': 500.0, ...},
                'USDT': {'total': 1000.0, 'free': 500.0, 'used': 500.0},
                ...
            }
        """
        pass
    
    @abstractmethod
    def create_order(
        self, 
        symbol: str, 
        order_type: str, 
        side: str, 
        amount: float, 
        price: Optional[float] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        trailing_stop: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        stop_loss_pct: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order.
        
        Args:
            symbol: Trading pair symbol
            order_type: Order type ('market', 'limit')
            side: Order side ('buy', 'sell')
            amount: Order amount/quantity
            price: Limit price (for limit orders)
            take_profit: Take profit price
            stop_loss: Stop loss price
            trailing_stop: Trailing stop distance
            take_profit_pct: Take profit as percentage (alternative to absolute price)
            stop_loss_pct: Stop loss as percentage (alternative to absolute price)
            
        Returns:
            Order info dictionary with 'id' field, or None on failure
        """
        pass
    
    @abstractmethod
    def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current ticker data.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with structure:
            {
                'last': 50000.0,
                'bid': 49999.0,
                'ask': 50001.0,
                'info': {...}  # Raw exchange data
            }
        """
        pass
    
    @abstractmethod
    def fetch_position(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current position for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with structure:
            {
                'size': 1.5,
                'side': 'Buy',  # 'Buy', 'Sell', or 'None'
                'entry_price': 50000.0
            }
        """
        pass
    
    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier (e.g., 10 for 10x)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> bool:
        """
        Close current position for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # Common helper methods (non-abstract)
    
    def get_market_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current market price, or None if unavailable
        """
        ticker = self.fetch_ticker(symbol)
        if ticker:
            return ticker.get('last')
        return None
    
    def format_amount(self, symbol: str, amount: float) -> str:
        """
        Format amount to exchange precision.
        This is a default implementation; subclasses may override.
        
        Args:
            symbol: Trading pair symbol
            amount: Amount to format
            
        Returns:
            Formatted amount as string
        """
        try:
            if self.exchange:
                return self.exchange.amount_to_precision(symbol, amount)
        except Exception as e:
            self.logger.warning(f"Could not format amount to precision: {e}")
        
        # Fallback to 3 decimals
        return f"{amount:.3f}"
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format to CCXT standard (BASE/QUOTE).
        
        Args:
            symbol: Symbol in any format
            
        Returns:
            Normalized symbol (e.g., 'BTC/USDT')
        """
        # If already in CCXT format, return as-is
        if '/' in symbol:
            return symbol
        
        # Common quote currencies to try
        quote_currencies = ['USDT', 'USD', 'BUSD', 'EUR', 'BTC', 'ETH']
        
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        
        # If we can't determine, return as-is and let the exchange handle it
        return symbol
    
    def denormalize_symbol(self, symbol: str) -> str:
        """
        Convert CCXT standard format to exchange-specific format.
        Default implementation removes the slash.
        
        Args:
            symbol: Symbol in CCXT format (e.g., 'BTC/USDT')
            
        Returns:
            Exchange-specific symbol format (e.g., 'BTCUSDT')
        """
        return symbol.replace('/', '')
    
    def _normalize_ohlcv_data(self, raw_data: List, reverse: bool = False) -> pd.DataFrame:
        """
        Normalize OHLCV data to standard DataFrame format.
        
        Args:
            raw_data: Raw OHLCV data from exchange
            reverse: Whether to reverse the data order
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if reverse:
            raw_data = list(reversed(raw_data))
        
        ohlcv = []
        for candle in raw_data:
            ohlcv.append([
                int(candle[0]),      # timestamp
                float(candle[1]),    # open
                float(candle[2]),    # high
                float(candle[3]),    # low
                float(candle[4]),    # close
                float(candle[5])     # volume
            ])
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            symbol: Trading pair symbol (optional for some exchanges)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def set_trailing_stop(self, symbol: str, trailing_stop_dist: float) -> bool:
        """
        Set trailing stop for current position.
        Optional method - not all exchanges support this.
        
        Args:
            symbol: Trading pair symbol
            trailing_stop_dist: Trailing stop distance
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.warning(f"Trailing stop not implemented for {self.__class__.__name__}")
        return False

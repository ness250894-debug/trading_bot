import ccxt
import pandas as pd
import logging
from .base_client import BaseExchangeClient


class CoinbaseClient(BaseExchangeClient):
    """Coinbase Advanced Trade API client implementation."""
    
    def __init__(self, api_key, api_secret, timeout=10000):
        """
        Initialize Coinbase exchange client.
        
        Args:
            api_key: API key
            api_secret: API secret
            timeout: Request timeout in milliseconds
        """
        super().__init__(api_key, api_secret, timeout=timeout)
        
        # Coinbase Advanced Trade (replaces Coinbase Pro)
        self.exchange = ccxt.coinbase({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': timeout,
        })
        
        # Load markets
        try:
            self.exchange.load_markets()
            self.logger.info("Coinbase client initialized")
        except Exception as e:
            self.logger.error(f"Failed to load Coinbase markets: {e}")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Fetch OHLCV data from Coinbase."""
        try:
            params = {}
            if since:
                params['start'] = since
            
            # Note: Coinbase may have limits on historical data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=min(limit, 300), params=params)
            return self._normalize_ohlcv_data(ohlcv)
            
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error fetching OHLCV: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV from Coinbase: {e}")
            raise
    
    def fetch_balance(self):
        """Fetch account balance from Coinbase."""
        try:
            balance = self.exchange.fetch_balance()
            
            # Normalize to standard format
            result = {
                'total': {},
                'free': {},
                'used': {},
                'info': balance.get('info', {})
            }
            
            for currency, amounts in balance.items():
                if isinstance(amounts, dict) and 'total' in amounts:
                    result['total'][currency] = amounts.get('total', 0.0)
                    result['free'][currency] = amounts.get('free', 0.0)
                    result['used'][currency] = amounts.get('used', 0.0)
                    result[currency] = amounts
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching balance from Coinbase: {e}")
            return None
    
    def create_order(
        self, 
        symbol, 
        order_type, 
        side, 
        amount, 
        price=None,
        take_profit=None,
        stop_loss=None,
        trailing_stop=None,
        take_profit_pct=None,
        stop_loss_pct=None
    ):
        """
        Create an order on Coinbase.
        
        Note: Coinbase primarily supports spot trading. 
        TP/SL orders may have limited support.
        """
        try:
            # Coinbase spot trading doesn't support leverage/futures like other exchanges
            # TP/SL are handled differently
            
            params = {}
            
            # Coinbase supports stop orders separately
            # For now, we'll create the main order and log TP/SL for future implementation
            if take_profit or stop_loss:
                self.logger.warning("Take profit and stop loss orders require separate order placement on Coinbase")
            
            # Create the main order
            if price:
                order = self.exchange.create_order(symbol, order_type, side, amount, price, params)
            else:
                order = self.exchange.create_order(symbol, order_type, side, amount, None, params)
            
            return order
            
        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Insufficient funds: {e}")
            return None
        except ccxt.InvalidOrder as e:
            self.logger.error(f"Invalid order: {e}")
            return None
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error creating order: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating order on Coinbase: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetch ticker data from Coinbase."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'last': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'info': ticker.get('info', {})
            }
        except Exception as e:
            self.logger.error(f"Error fetching ticker from Coinbase: {e}")
            return None
    
    def fetch_position(self, symbol):
        """
        Fetch current position from Coinbase.
        
        Note: Coinbase primarily supports spot trading, not futures/margin.
        This returns a simplified position based on balance.
        """
        try:
            # Coinbase is primarily spot trading
            # We can approximate "position" by checking balance of base currency
            base_currency = symbol.split('/')[0] if '/' in symbol else symbol[:3]
            
            balance = self.fetch_balance()
            if balance and base_currency in balance:
                amount = balance[base_currency].get('total', 0.0)
                
                if amount > 0:
                    return {
                        'size': amount,
                        'side': 'Buy',  # Spot holdings are considered "long"
                        'entry_price': 0.0  # Not tracked for spot
                    }
            
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error fetching position from Coinbase: {e}")
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
    
    def set_leverage(self, symbol, leverage):
        """
        Set leverage for a symbol on Coinbase.
        
        Note: Coinbase spot trading doesn't support leverage.
        This is a no-op that returns True for compatibility.
        """
        if leverage > 1:
            self.logger.warning(f"Coinbase spot trading does not support leverage. Ignoring leverage={leverage}")
        return True
    
    def close_position(self, symbol):
        """
        Close current position for a symbol on Coinbase.
        
        For spot trading, this means selling all held base currency.
        """
        try:
            position = self.fetch_position(symbol)
            size = position.get('size', 0.0)
            
            if size > 0:
                self.logger.info(f"Selling {size} {symbol} (spot close)...")
                
                # Sell all holdings
                return self.create_order(
                    symbol=symbol,
                    order_type='market',
                    side='sell',
                    amount=size
                )
            else:
                self.logger.info(f"No position to close for {symbol}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error closing position on Coinbase: {e}")
            return False
    
    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """
        Set trailing stop for current position on Coinbase.
        
        Note: Limited support for trailing stops on Coinbase spot trading.
        """
        self.logger.warning("Trailing stops have limited support on Coinbase spot trading")
        return False

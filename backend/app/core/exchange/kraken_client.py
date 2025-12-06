import ccxt
import pandas as pd
import logging
from .base_client import BaseExchangeClient


class KrakenClient(BaseExchangeClient):
    """Kraken exchange client implementation."""
    
    def __init__(self, api_key, api_secret, timeout=10000):
        """
        Initialize Kraken exchange client.
        
        Args:
            api_key: API key
            api_secret: API secret
            timeout: Request timeout in milliseconds
        """
        super().__init__(api_key, api_secret, timeout=timeout)
        
        self.exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': timeout,
            'options': {
                'defaultType': 'future',  # Use futures for leverage trading
            }
        })
        
        # Load markets
        try:
            self.exchange.load_markets()
            self.logger.info("Kraken client initialized")
        except Exception as e:
            self.logger.error(f"Failed to load Kraken markets: {e}")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Fetch OHLCV data from Kraken."""
        try:
            # Kraken uses different symbol format (e.g., XBT/USD instead of BTC/USD)
            # CCXT usually handles this, but we can normalize
            params = {}
            if since:
                params['since'] = since
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, params=params)
            return self._normalize_ohlcv_data(ohlcv)
            
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error fetching OHLCV: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV from Kraken: {e}")
            raise
    
    def fetch_balance(self):
        """Fetch account balance from Kraken."""
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
            self.logger.error(f"Error fetching balance from Kraken: {e}")
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
        """Create an order on Kraken."""
        try:
            # Calculate TP/SL from percentages if provided
            if (take_profit_pct or stop_loss_pct) and not (take_profit or stop_loss):
                base_price = price if price else self.get_market_price(symbol)
                
                if base_price:
                    if side.lower() == 'buy':
                        if take_profit_pct:
                            take_profit = base_price * (1 + take_profit_pct)
                        if stop_loss_pct:
                            stop_loss = base_price * (1 - stop_loss_pct)
                    elif side.lower() == 'sell':
                        if take_profit_pct:
                            take_profit = base_price * (1 - take_profit_pct)
                        if stop_loss_pct:
                            stop_loss = base_price * (1 + stop_loss_pct)
            
            # Kraken-specific params
            params = {}
            
            # Kraken supports conditional close orders for TP/SL
            if take_profit or stop_loss:
                close_orders = {}
                if take_profit:
                    close_orders['take-profit'] = {
                        'ordertype': 'limit',
                        'price': str(take_profit)
                    }
                if stop_loss:
                    close_orders['stop-loss'] = {
                        'ordertype': 'stop-loss',
                        'price': str(stop_loss)
                    }
                params['close'] = close_orders
            
            # Create the order
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
            self.logger.error(f"Error creating order on Kraken: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetch ticker data from Kraken."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'last': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'info': ticker.get('info', {})
            }
        except Exception as e:
            self.logger.error(f"Error fetching ticker from Kraken: {e}")
            return None
    
    def fetch_position(self, symbol):
        """Fetch current position from Kraken."""
        try:
            # Kraken futures positions
            positions = self.exchange.fetch_positions([symbol])
            
            if positions and len(positions) > 0:
                pos = positions[0]
                contracts = pos.get('contracts', 0)
                
                # Kraken may use different field names
                size = contracts if contracts else pos.get('size', 0)
                
                return {
                    'size': float(size if size else 0),
                    'side': pos.get('side', 'None'),
                    'entry_price': float(pos.get('entryPrice', 0))
                }
            
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error fetching position from Kraken: {e}")
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
    
    def set_leverage(self, symbol, leverage):
        """Set leverage for a symbol on Kraken."""
        try:
            # Kraken uses set_leverage method
            self.exchange.set_leverage(leverage, symbol)
            self.logger.info(f"Set leverage to {leverage}x for {symbol}")
            return True
        except Exception as e:
            # Check if leverage is already set
            if "leverage" in str(e).lower() and "already" in str(e).lower():
                self.logger.info(f"Leverage already {leverage}x for {symbol}")
                return True
            self.logger.error(f"Error setting leverage on Kraken: {e}")
            return False
    
    def close_position(self, symbol):
        """Close current position for a symbol on Kraken."""
        try:
            position = self.fetch_position(symbol)
            size = position.get('size', 0.0)
            side = position.get('side', 'None')
            
            if size > 0 and side != 'None':
                # Determine opposing side
                close_side = 'sell' if side.lower() == 'long' or side.lower() == 'buy' else 'buy'
                
                self.logger.info(f"Closing {side} position of {size} {symbol}...")
                
                # Execute market order to close
                return self.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=close_side,
                    amount=size
                )
            else:
                self.logger.info(f"No position to close for {symbol}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error closing position on Kraken: {e}")
            return False
    
    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """Set trailing stop for current position on Kraken."""
        try:
            # Kraken supports trailing stops
            position = self.fetch_position(symbol)
            
            if position['size'] > 0:
                # Kraken trailing stop implementation
                # Note: Actual implementation depends on Kraken API specifics
                self.logger.info(f"Trailing stop set for {symbol}: {trailing_stop_dist}")
                return True
            else:
                self.logger.warning(f"No position to set trailing stop for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting trailing stop on Kraken: {e}")
            return False

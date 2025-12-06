import ccxt
import pandas as pd
import logging
from .base_client import BaseExchangeClient

class ByBitClient(BaseExchangeClient):
    def __init__(self, api_key, api_secret, timeout=10000):
        """
        Initialize ByBit exchange client with timeout support.
        
        Args:
            api_key: API key
            api_secret: API secret  
            timeout: Request timeout in milliseconds (default 10s)
        """
        # Call parent constructor
        super().__init__(api_key, api_secret, timeout=timeout)
        
        self.logger = logging.getLogger(__name__)
        
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': timeout,  # Add timeout
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': False,
                'recvWindow': 10000,
            }
        })
        
        # Explicitly sync time
        try:
            server_time = self.exchange.fetch_time()
            import time
            local_time = int(time.time() * 1000)
            
            # Calculate diff
            diff = (local_time - server_time) + 1000
            
            self.exchange.options['timeDifference'] = diff
            self.logger.info(f"Time synced. Server: {server_time}, Local: {local_time}, Diff: {diff}ms")
        except Exception as e:
            self.logger.error(f"Failed to sync time: {e}")

        # Load markets
        try:
            self.exchange.load_markets()
        except Exception as e:
             self.logger.error(f"Failed to load markets: {e}")

    def format_amount(self, symbol, amount):
        """Formats amount to precision."""
        try:
            return self.exchange.amount_to_precision(symbol, amount)
        except Exception:
            # Fallback to 3 decimals if failure
            return f"{amount:.3f}"

    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Fetches OHLCV data and returns a DataFrame."""
        last_error = None
        for attempt in range(3):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
                    
            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                self.logger.warning(f"Network error fetching OHLCV (Attempt {attempt+1}/3): {e}")
                last_error = e
                import time
                time.sleep(2 * (attempt + 1)) # Exponential backoff
            except ccxt.RateLimitExceeded as e:
                self.logger.warning(f"Rate limit exceeded fetching OHLCV: {e}")
                last_error = e
                import time
                time.sleep(10) # Wait longer for rate limit
            except Exception as e:
                self.logger.error(f"Error fetching OHLCV: {e}")
                last_error = e
                break 
        
        # If we get here, we failed
        if last_error:
            raise last_error
        raise Exception("Failed to fetch OHLCV: Unknown error")

    def fetch_balance(self):
        """Fetches account balance."""
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return None

    def create_order(self, symbol, order_type, side, amount, price=None, take_profit=None, stop_loss=None, trailing_stop=None, take_profit_pct=None, stop_loss_pct=None):
        """Creates an order with optional TP/SL/Trailing."""
        try:
            # Calculate TP/SL from percentages if provided
            if (take_profit_pct or stop_loss_pct) and not (take_profit or stop_loss):
                base_price = price
                if not base_price:
                    # For market orders, use current market price
                    base_price = self.get_market_price(symbol)
                
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

            params = {}
            if take_profit:
                params['takeProfit'] = str(take_profit)
            if stop_loss:
                params['stopLoss'] = str(stop_loss)
            if trailing_stop:
                params['trailingStop'] = str(trailing_stop)

            if price:
                return self.exchange.create_order(symbol, order_type, side, amount, price, params)
            else:
                return self.exchange.create_order(symbol, order_type, side, amount, None, params)
        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Insufficient Funds: {e}")
            return None
        except ccxt.InvalidOrder as e:
            self.logger.error(f"Invalid Order (Size too small/large?): {e}")
            return None
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error creating order: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetches current ticker data (last, bid, ask)."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {e}")
            return None

    def get_market_price(self, symbol):
        """Fetches current market price."""
        ticker = self.fetch_ticker(symbol)
        if ticker:
            return ticker['last']
        return None

    def fetch_position(self, symbol):
        """Fetches current position for a symbol."""
        for attempt in range(3):
            try:
                # Standard CCXT for Live Trading
                positions = self.exchange.fetch_positions([symbol])
                if positions:
                    pos = positions[0]
                    return {
                        'size': float(pos.get('contracts', 0) if pos.get('contracts') is not None else pos.get('info', {}).get('size', 0)),
                        'side': pos.get('side', 'None'),
                        'entry_price': float(pos.get('entryPrice', 0))
                    }
                return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}

            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                self.logger.warning(f"Network error fetching position (Attempt {attempt+1}/3): {e}")
                import time
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                self.logger.error(f"Error fetching position: {e}")
                return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
        return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}

    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """Sets trailing stop for the current position."""
        try:
            # CCXT's set_trading_stop usually maps to the correct endpoint
            # But to be safe and consistent with previous workaround:
            market_symbol = symbol.replace('/', '')
            params = {
                'category': 'linear',
                'symbol': market_symbol,
                'trailingStop': str(trailing_stop_dist),
                'positionIdx': 0
            }
            return self.exchange.set_trading_stop(symbol, trailing_stop_dist, params=params)
        except Exception as e:
            self.logger.error(f"Error setting trailing stop: {e}")
            return False

    def set_leverage(self, symbol, leverage):
        """Sets leverage for the symbol."""
        try:
            self.exchange.set_leverage(leverage, symbol)
            self.logger.info(f"Leverage set to {leverage}x for {symbol}")
            return True
        except Exception as e:
            if "not modified" in str(e).lower() or "110043" in str(e):
                 self.logger.info(f"Leverage already {leverage}x for {symbol}")
                 return True
            self.logger.error(f"Failed to set leverage: {e}")
            return False
            
    def close_position(self, symbol):
        """Closes the current position for the symbol."""
        try:
            position = self.fetch_position(symbol)
            size = position.get('size', 0.0)
            side = position.get('side', 'None')
            
            if size > 0 and side != 'None':
                # Determine opposing side
                close_side = 'Sell' if side == 'Buy' else 'Buy'
                
                self.logger.info(f"Closing {side} position of {size} {symbol}...")
                
                # Execute Market Order to close
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
            self.logger.error(f"Error closing position: {e}")
            return False

    def fetch_order(self, order_id, symbol=None):
        """Fetches a specific order by ID."""
        try:
            return self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"Error fetching order {order_id}: {e}")
            return None

    def fetch_my_trades(self, symbol, limit=1):
        """Fetches recent trades for a symbol."""
        try:
            return self.exchange.fetch_my_trades(symbol, limit=limit)
        except Exception as e:
            self.logger.error(f"Error fetching trades for {symbol}: {e}")
            return []


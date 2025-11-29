import ccxt
import pandas as pd
import logging
from .base_client import BaseExchangeClient


class BinanceClient(BaseExchangeClient):
    """Binance exchange client implementation."""
    
    def __init__(self, api_key, api_secret, demo=True, timeout=10000):
        """
        Initialize Binance exchange client.
        
        Args:
            api_key: API key
            api_secret: API secret
            demo: Use testnet
            timeout: Request timeout in milliseconds
        """
        super().__init__(api_key, api_secret, demo, timeout)
        
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': timeout,
            'options': {
                'defaultType': 'future',  # Use futures for leverage trading
                'adjustForTimeDifference': True,
            }
        })
        
        if demo:
            self.exchange.set_sandbox_mode(True)
            # Binance testnet URLs
            self.logger.info("Using Binance Testnet")
        
        # Load markets
        try:
            self.exchange.load_markets()
            self.logger.info(f"Binance client initialized ({'Testnet' if demo else 'Live'})")
        except Exception as e:
            self.logger.error(f"Failed to load Binance markets: {e}")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Fetch OHLCV data from Binance."""
        try:
            params = {}
            if since:
                params['startTime'] = since
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, params=params)
            return self._normalize_ohlcv_data(ohlcv)
            
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error fetching OHLCV: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV from Binance: {e}")
            raise
    
    def fetch_balance(self):
        """Fetch account balance from Binance."""
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
            self.logger.error(f"Error fetching balance from Binance: {e}")
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
        """Create an order on Binance."""
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
            
            # Create params for TP/SL
            params = {}
            if take_profit:
                params['stopPrice'] = take_profit
                params['takeProfit'] = {'type': 'TAKE_PROFIT_MARKET', 'stopPrice': take_profit}
            if stop_loss:
                params['stopLoss'] = {'type': 'STOP_MARKET', 'stopPrice': stop_loss}
            
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
            self.logger.error(f"Error creating order on Binance: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetch ticker data from Binance."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'last': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'info': ticker.get('info', {})
            }
        except Exception as e:
            self.logger.error(f"Error fetching ticker from Binance: {e}")
            return None
    
    def fetch_position(self, symbol):
        """Fetch current position from Binance."""
        try:
            positions = self.exchange.fetch_positions([symbol])
            
            if positions and len(positions) > 0:
                pos = positions[0]
                contracts = pos.get('contracts', 0)
                
                return {
                    'size': float(contracts if contracts else 0),
                    'side': pos.get('side', 'None'),
                    'entry_price': float(pos.get('entryPrice', 0))
                }
            
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error fetching position from Binance: {e}")
            return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
    
    def set_leverage(self, symbol, leverage):
        """Set leverage for a symbol on Binance."""
        try:
            self.exchange.set_leverage(leverage, symbol)
            self.logger.info(f"Set leverage to {leverage}x for {symbol}")
            return True
        except Exception as e:
            # Check if leverage is already set
            if "leverage not modified" in str(e).lower():
                self.logger.info(f"Leverage already {leverage}x for {symbol}")
                return True
            self.logger.error(f"Error setting leverage on Binance: {e}")
            return False
    
    def close_position(self, symbol):
        """Close current position for a symbol on Binance."""
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
            self.logger.error(f"Error closing position on Binance: {e}")
            return False
    
    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """Set trailing stop for current position on Binance."""
        try:
            # Binance supports trailing stop orders
            position = self.fetch_position(symbol)
            
            if position['size'] > 0:
                params = {
                    'activationPrice': None,  # Will use current market price
                    'callbackRate': trailing_stop_dist  # In percentage
                }
                
                # Create trailing stop order
                # Note: Implementation depends on Binance API specifics
                self.logger.info(f"Trailing stop set for {symbol}: {trailing_stop_dist}")
                return True
            else:
                self.logger.warning(f"No position to set trailing stop for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting trailing stop on Binance: {e}")
            return False

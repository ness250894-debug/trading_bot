import logging
from .base_client import BaseExchangeClient
from .exchange_factory import ExchangeFactory
from .. import config

logger = logging.getLogger("PaperExchange")

class PaperExchange(BaseExchangeClient):
    def __init__(self, api_key, api_secret, initial_balance=1000.0, exchange_type='bybit'):
        """
        Initialize paper trading exchange.
        
        Args:
            api_key: API key (used for data fetching)
            api_secret: API secret (used for data fetching)
            initial_balance: Starting virtual balance
            exchange_type: Which exchange to use for data fetching ('bybit', 'binance', etc.)
        """
        # Initialize base class
        super().__init__(api_key, api_secret, demo=True)
        
        # Create real client for data fetching (using factory)
        self.data_client = ExchangeFactory.create_exchange(
            exchange_type, api_key, api_secret, demo=True
        )
        
        # Virtual State
        self.paper_balance = initial_balance
        self.paper_positions = {} # {symbol: {'size': 0.0, 'entry_price': 0.0, 'side': 'None'}}
        self.orders = []
        
        logger.info(f"Paper Exchange initialized with ${self.paper_balance:.2f} using {exchange_type}")

    # Override abstract methods to use virtual state
    
    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Delegate to real exchange for market data."""
        return self.data_client.fetch_ohlcv(symbol, timeframe, limit, since)
    
    def fetch_ticker(self, symbol):
        """Delegate to real exchange for ticker data."""
        return self.data_client.fetch_ticker(symbol)

    def fetch_balance(self):
        """Returns virtual balance in the expected format."""
        # Mimic CCXT/ByBit structure
        return {
            'total': {'USDT': self.paper_balance},
            'free': {'USDT': self.paper_balance}, # Simplified: assuming all free for now
            'used': {'USDT': 0.0},
            'USDT': {'total': self.paper_balance, 'free': self.paper_balance, 'used': 0.0}
        }

    def fetch_position(self, symbol):
        """Returns virtual position for symbol."""
        pos = self.paper_positions.get(symbol, {'size': 0.0, 'side': 'None', 'entry_price': 0.0})
        return pos

    def create_order(self, symbol, order_type, side, amount, price=None, take_profit=None, stop_loss=None, trailing_stop=None, take_profit_pct=None, stop_loss_pct=None):
        """Executes a virtual order."""
        try:
            current_price = price if price else self.get_market_price(symbol)
            if not current_price:
                logger.error("Could not get market price for paper order.")
                return None

            value = amount * current_price
            fee = value * config.TAKER_FEE_PCT
            
            # Update Balance (Deduct fee)
            self.paper_balance -= fee
            
            # Update Position
            pos = self.paper_positions.get(symbol, {'size': 0.0, 'side': 'None', 'entry_price': 0.0})
            
            if side == 'buy':
                if pos['side'] == 'Sell': # Closing Short
                    # Calculate PnL
                    pnl = (pos['entry_price'] - current_price) * amount # Simplified: assuming full close
                    self.paper_balance += pnl
                    
                    new_size = pos['size'] - amount
                    if new_size <= 0:
                         self.paper_positions[symbol] = {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
                    else:
                         # Partial close (not fully supported in this simple logic yet)
                         pos['size'] = new_size
                         self.paper_positions[symbol] = pos
                         
                else: # Opening/Adding Long
                    # Weighted average entry price
                    total_cost = (pos['size'] * pos['entry_price']) + (amount * current_price)
                    new_size = pos['size'] + amount
                    avg_price = total_cost / new_size
                    
                    self.paper_positions[symbol] = {
                        'size': new_size,
                        'side': 'Buy',
                        'entry_price': avg_price
                    }
                    
            elif side == 'sell':
                if pos['side'] == 'Buy': # Closing Long
                    # Calculate PnL
                    pnl = (current_price - pos['entry_price']) * amount
                    self.paper_balance += pnl
                    
                    new_size = pos['size'] - amount
                    if new_size <= 0:
                         self.paper_positions[symbol] = {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
                    else:
                         pos['size'] = new_size
                         self.paper_positions[symbol] = pos
                         
                else: # Opening/Adding Short
                    total_cost = (pos['size'] * pos['entry_price']) + (amount * current_price)
                    new_size = pos['size'] + amount
                    avg_price = total_cost / new_size
                    
                    self.paper_positions[symbol] = {
                        'size': new_size,
                        'side': 'Sell',
                        'entry_price': avg_price
                    }

            logger.info(f"PAPER ORDER: {side.upper()} {amount} {symbol} @ {current_price:.2f} | Fee: {fee:.4f} | Bal: {self.paper_balance:.2f}")
            
            # Return fake order ID
            import uuid
            return {'id': str(uuid.uuid4()), 'info': {'paper': True}}
            
        except Exception as e:
            logger.error(f"Error creating paper order: {e}")
            return None

    def set_leverage(self, symbol, leverage):
        """Virtual leverage setting (just logs for now)."""
        logger.info(f"PAPER: Set leverage {leverage}x for {symbol}")
        return True

    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """Virtual trailing stop (just logs for now)."""
        logger.info(f"PAPER: Set trailing stop {trailing_stop_dist} for {symbol}")
        return True
    
    def close_position(self, symbol):
        """Close virtual position."""
        pos = self.fetch_position(symbol)
        size = pos.get('size', 0.0)
        side = pos.get('side', 'None')
        
        if size > 0 and side != 'None':
            # Determine opposing side
            close_side = 'sell' if side == 'Buy' else 'buy'
            
            logger.info(f"PAPER: Closing {side} position of {size} {symbol}...")
            
            # Execute virtual close order
            return self.create_order(
                symbol=symbol,
                order_type='market',
                side=close_side,
                amount=size
            )
        else:
            logger.info(f"PAPER: No position to close for {symbol}")
            return True


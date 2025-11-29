import pandas as pd
import logging
from .exchange import ExchangeClient
from . import config
from .strategies.mean_reversion import MeanReversion
from .strategies.sma_crossover import SMACrossover
from .strategies.macd import MACDStrategy
from .strategies.rsi import RSIStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorizedBacktester")

# Improved VectorizedBacktester with proper tracking
class VectorizedBacktester:
    def __init__(self, symbol, timeframe, strategy, days=5, data=None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days = days
        self.days = days
        self.client = None
        if data is None:
            self.client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=getattr(config, 'DEMO', True))
        
        if isinstance(strategy, str):
            self.strategy_name = strategy
            self.strategy = self._load_strategy(strategy)
        else:
            self.strategy = strategy
            self.strategy_name = strategy.__class__.__name__

        self.df = data
        self.balance = 1000.0
        self.position_size = 0
        self.entry_price = 0
        self.trades = []

    def _load_strategy(self, name):
        if name == 'mean_reversion': return MeanReversion()
        if name == 'sma_crossover': return SMACrossover()
        if name == 'macd': return MACDStrategy()
        if name == 'rsi': return RSIStrategy()
        return MeanReversion()

    def fetch_data(self):
        if self.df is not None and not self.df.empty:
            return

        logger.info(f"Fetching {self.days} days of data for {self.symbol}...")
        self.df = self.client.fetch_ohlcv(self.symbol, self.timeframe, limit=1000)

    def run(self):
        if self.df is None: return

        # 1. Populate
        self.df = self.strategy.populate_indicators(self.df)
        self.df = self.strategy.populate_buy_trend(self.df)
        self.df = self.strategy.populate_sell_trend(self.df)
        
        # 2. Loop
        for i, row in self.df.iterrows():
            price = row['close']
            ts = row['timestamp']
            
            if self.position_size > 0:
                # Check Exit
                reason = None
                exit_price = price
                
                if row.get('sell') == 1:
                    reason = 'Signal'
                elif row['low'] <= self.entry_price * (1 - config.STOP_LOSS_PCT):
                    reason = 'Stop Loss'
                    exit_price = self.entry_price * (1 - config.STOP_LOSS_PCT)
                elif row['high'] >= self.entry_price * (1 + config.TAKE_PROFIT_PCT):
                    reason = 'Take Profit'
                    exit_price = self.entry_price * (1 + config.TAKE_PROFIT_PCT)
                
                # Trailing Stop Logic
                if not reason:
                    # Update High/Low for Trailing Stop
                    if not hasattr(self, 'highest_price') or row['high'] > self.highest_price:
                        self.highest_price = row['high']
                    
                    # Check Activation
                    if self.highest_price >= self.entry_price * (1 + config.TRAILING_STOP_ACTIVATION_PCT):
                        stop_price = self.highest_price * (1 - config.TRAILING_STOP_PCT)
                        if row['low'] < stop_price:
                            reason = 'Trailing Stop'
                            exit_price = stop_price

                
                if reason:
                    # Close
                    value = self.position_size * exit_price
                    fee = value * config.TAKER_FEE_PCT
                    pnl = (exit_price - self.entry_price) * self.position_size
                    self.balance += pnl - fee
                    self.trades.append({'pnl': pnl - fee, 'reason': reason, 'time': ts})
                    self.position_size = 0
                    self.highest_price = 0  # Reset tracking
            
            elif self.position_size == 0:
                if row.get('buy') == 1:
                    # Open
                    amount_usdt = self.balance * 0.99
                    self.position_size = amount_usdt / price
                    self.entry_price = price
                    self.highest_price = price  # Initialize tracking
                    fee = amount_usdt * config.TAKER_FEE_PCT
                    self.balance -= fee

    def show_results(self):
        logger.info(f"Final Balance: {self.balance:.2f}")
        logger.info(f"Trades: {len(self.trades)}")

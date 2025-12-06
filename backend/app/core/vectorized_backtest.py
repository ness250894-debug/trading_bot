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
            self.client = ExchangeClient(config.API_KEY, config.API_SECRET)
        
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

        # 1. Populate Indicators
        self.df = self.strategy.populate_indicators(self.df)
        self.df = self.strategy.populate_buy_trend(self.df)
        self.df = self.strategy.populate_sell_trend(self.df)
        
        # 2. Prepare Numpy Arrays for Speed
        # We drop NaNs to ensure alignment
        # df_clean = self.df.dropna().reset_index(drop=True)
        # Actually, let's keep NaNs but handle them, to preserve timestamps
        
        opens = self.df['open'].to_numpy()
        highs = self.df['high'].to_numpy()
        lows = self.df['low'].to_numpy()
        closes = self.df['close'].to_numpy()
        timestamps = self.df['timestamp'].to_numpy()
        
        # Handle cases where buy/sell columns might not exist if strategy didn't set them
        if 'buy' not in self.df.columns: self.df['buy'] = 0
        if 'sell' not in self.df.columns: self.df['sell'] = 0
        
        buy_signals = self.df['buy'].fillna(0).to_numpy()
        sell_signals = self.df['sell'].fillna(0).to_numpy()
        
        n = len(closes)
        in_position = False
        entry_price = 0.0
        highest_price = 0.0 # For trailing stop
        
        # 3. Vectorized Loop (Iterating index)
        # We start at i=1 because signals from i-1 execute at Open of i
        for i in range(1, n):
            # Check Exit First
            if in_position:
                exit_reason = None
                exit_price = 0.0
                
                # A. Signal Exit (from previous candle i-1)
                if sell_signals[i-1] == 1:
                    exit_reason = 'Signal'
                    exit_price = opens[i] # Execute at Open
                
                # B. Stop Loss / Take Profit (intra-candle check)
                # We assume worst-case (hit SL first) or checked against High/Low
                # Current Candle High/Low
                elif lows[i] <= entry_price * (1 - config.STOP_LOSS_PCT):
                    exit_reason = 'Stop Loss'
                    # Slippage simulation: realistic worst case execution
                    exit_price = entry_price * (1 - config.STOP_LOSS_PCT)
                
                elif highs[i] >= entry_price * (1 + config.TAKE_PROFIT_PCT):
                    exit_reason = 'Take Profit'
                    exit_price = entry_price * (1 + config.TAKE_PROFIT_PCT)
                
                # C. Trailing Stop
                else:
                    # Update High for Trailing Stop
                    if highs[i] > highest_price:
                        highest_price = highs[i]
                    
                    activation_price = entry_price * (1 + config.TRAILING_STOP_ACTIVATION_PCT)
                    if highest_price >= activation_price:
                        stop_price = highest_price * (1 - config.TRAILING_STOP_PCT)
                        if lows[i] < stop_price:
                            exit_reason = 'Trailing Stop'
                            exit_price = stop_price

                # Execute Exit
                if exit_reason:
                    # Calculate PnL
                    # Simulated Amount: 99% of balance
                    # position_size = (balance * 0.99) / entry_price
                    # We track balance continuously
                    
                    # Re-calculate position size based on balance at entry time?
                    # Simplify: We held 'position_size' units
                    
                    value = self.position_size * exit_price
                    fee = value * config.TAKER_FEE_PCT
                    pnl = (exit_price - entry_price) * self.position_size
                    
                    self.balance += pnl - fee
                    
                    self.trades.append({
                        'pnl': pnl - fee,
                        'reason': exit_reason,
                        'time': timestamps[i], # Execution time
                        'entry_price': entry_price,
                        'exit_price': exit_price
                    })
                    
                    in_position = False
                    self.position_size = 0.0
                    entry_price = 0.0
                    highest_price = 0.0

            # Check Entry (if not in position)
            # Use 'elif' because we can't enter same candle we exited (simplification)
            elif not in_position:
                if buy_signals[i-1] == 1:
                    # Execute BUY at Open of i
                    entry_price = opens[i]
                    amount_usdt = self.balance * 0.99
                    fee = amount_usdt * config.TAKER_FEE_PCT
                    
                    self.balance -= fee
                    self.position_size = amount_usdt / entry_price
                    highest_price = entry_price
                    in_position = True

    def show_results(self):
        logger.info(f"Final Balance: {self.balance:.2f}")
        logger.info(f"Trades: {len(self.trades)}")

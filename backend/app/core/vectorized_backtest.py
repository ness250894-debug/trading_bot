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
# Improved VectorizedBacktester with proper tracking
class VectorizedBacktester:
    def __init__(self, symbol, timeframe, strategy, days=5, data=None, leverage=1.0):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days = days
        self.leverage = float(leverage)
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
        
        # Get TP/SL from strategy if available, else config
        take_profit_pct = getattr(self.strategy, 'take_profit_pct', config.TAKE_PROFIT_PCT)
        stop_loss_pct = getattr(self.strategy, 'stop_loss_pct', config.STOP_LOSS_PCT)
        
        # 3. Vectorized Loop (Iterating index)
        # We start at i=1 because signals from i-1 execute at Open of i
        for i in range(1, n):
            # Check Exit First
            if in_position:
                exit_reason = None
                exit_price = 0.0
                
                # Liquidation Check (Approximation)
                # Liq Price = Entry * (1 - 1/Leverage)
                # If Margin Ratio is dangerous. 
                liq_price = entry_price * (1 - (1.0 / self.leverage))
                if lows[i] <= liq_price:
                     exit_reason = 'Liquidation'
                     exit_price = liq_price

                # A. Signal Exit (from previous candle i-1)
                elif sell_signals[i-1] == 1:
                    exit_reason = 'Signal'
                    exit_price = opens[i] # Execute at Open
                
                # B. Stop Loss / Take Profit (intra-candle check)
                elif lows[i] <= entry_price * (1 - stop_loss_pct):
                    exit_reason = 'Stop Loss'
                    exit_price = entry_price * (1 - stop_loss_pct)
                
                elif highs[i] >= entry_price * (1 + take_profit_pct):
                    exit_reason = 'Take Profit'
                    exit_price = entry_price * (1 + take_profit_pct)
                
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
                    # If liquidated, lose entire margin
                    if exit_reason == 'Liquidation':
                        pnl = - (self.balance * 0.99) # Lose the margin
                        fee = 0 # Usually valid to assume lost margin covers fees or simplified
                        exit_price = liq_price
                    else:
                        value = self.position_size * exit_price
                        fee = value * config.TAKER_FEE_PCT
                        pnl = (exit_price - entry_price) * self.position_size
                    
                    self.balance += float(pnl - fee)
                    
                    self.trades.append({
                        'pnl': float(pnl - fee),
                        'reason': str(exit_reason),
                        'time': str(timestamps[i]),
                        'entry_price': float(entry_price),
                        'exit_price': float(exit_price),
                        'leverage': self.leverage
                    })
                    
                    in_position = False
                    self.position_size = 0.0
                    entry_price = 0.0
                    highest_price = 0.0

            # Check Entry (if not in position)
            elif not in_position:
                if buy_signals[i-1] == 1:
                    # Execute BUY at Open of i
                    entry_price = opens[i]
                    
                    # Margin Model: 
                    # We invest 99% of available balance as Margin
                    margin = self.balance * 0.99
                    
                    if margin <= 0: break # Bankrupt

                    fee = (margin * self.leverage) * config.TAKER_FEE_PCT
                    
                    # Update Balance (deduct fee immediately? or from PnL? simpler to deduct fee from balance)
                    self.balance -= float(fee)
                    
                    # Position Size (Total Value in Coins) = (Margin * Leverage) / Price
                    self.position_size = (margin * self.leverage) / entry_price
                    
                    highest_price = entry_price
                    in_position = True

    def show_results(self):
        logger.info(f"Final Balance: {self.balance:.2f}")
        logger.info(f"Trades: {len(self.trades)}")

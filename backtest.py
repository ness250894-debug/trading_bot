import pandas as pd
import logging
from exchange.client import ExchangeClient
import config
from strategies.mean_reversion import MeanReversion
from strategies.sma_crossover import SMACrossover
from strategies.macd import MACDStrategy
from strategies.rsi import RSIStrategy


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Backtester")

class Backtester:
    def __init__(self, symbol, timeframe, strategy, days=5, data=None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days = days
        self.client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=True) # Use Demo for data fetching
        
        if isinstance(strategy, str):
            self.strategy_name = strategy
            self.strategy = self._load_strategy(strategy)
        else:
            self.strategy = strategy
            self.strategy_name = strategy.__class__.__name__

        self.df = data
        self.balance = 1000.0 # Initial Balance
        self.position = 0.0
        self.entry_price = 0.0
        self.trades = []
        self.error = None

    def _load_strategy(self, name):
        if name == 'mean_reversion': return MeanReversion()
        if name == 'sma_crossover': return SMACrossover()
        if name == 'macd': return MACDStrategy()
        if name == 'rsi': return RSIStrategy()
        return MeanReversion()

    def fetch_data(self):
        if self.df is not None and not self.df.empty:
            logger.info("Data already loaded.")
            return

        logger.info(f"Fetching {self.days} days of data for {self.symbol} ({self.timeframe})...")
        
        # Calculate start time (ms)
        import time
        now = int(time.time() * 1000)
        start_time = now - (self.days * 24 * 60 * 60 * 1000)
        
        all_dfs = []
        current_time = start_time
        
        while True:
            # Fetch batch
            # Limit is 1000 for ByBit
            try:
                batch_df = self.client.fetch_ohlcv(self.symbol, self.timeframe, limit=1000, since=current_time)
            except Exception as e:
                self.error = str(e)
                logger.error(f"Failed to fetch data: {e}")
                break
            
            if batch_df is None or batch_df.empty:
                break
            
            all_dfs.append(batch_df)
            
            # Get last timestamp
            last_timestamp = batch_df.iloc[-1]['timestamp']
            last_ts_ms = int(last_timestamp.timestamp() * 1000)
            
            # Check if we reached now
            if last_ts_ms >= now:
                break
                
            # Check if we got less than limit (end of data)
            if len(batch_df) < 1000:
                break
            
            # Next batch starts after the last candle
            # ByBit 'start' is inclusive, so we add 1ms (or small buffer) to avoid duplicate
            # But safer to just filter duplicates later
            current_time = last_ts_ms + 1
            
            # Safety break
            if current_time >= now:
                break
                
        if all_dfs:
            self.df = pd.concat(all_dfs)
            self.df = self.df.drop_duplicates(subset=['timestamp']).sort_values(by='timestamp').reset_index(drop=True)
            logger.info(f"Loaded {len(self.df)} candles total.")
        else:
            if not self.error:
                self.error = "No data found for the specified parameters."
            logger.error("Failed to load data.")

    def run(self):
        if self.df is None:
            logger.error("No data to backtest.")
            return

        logger.info(f"Running backtest with {self.strategy_name}...")
        
        # Pre-calculate indicators for the entire dataframe
        logger.info("Calculating indicators...")
        self.df = self.strategy.calculate_indicators(self.df)
        
        total_candles = len(self.df)
        
        for i in range(50, total_candles): # Start after some warmup period
            # Get current row
            current_row = self.df.iloc[i]
            current_price = current_row['close']
            timestamp = current_row['timestamp']
            
            # Check Signal
            result = self.strategy.check_signal(current_row)
            signal = result['signal']
            
            # Execute Trade
            if signal == 'BUY':
                if self.position == 0:
                    self._open_position('long', current_price, timestamp)
                elif self.position < 0: # Close Short
                    self._close_position(current_price, timestamp)
                    self._open_position('long', current_price, timestamp)
                    
            elif signal == 'SELL':
                if self.position == 0:
                    self._open_position('short', current_price, timestamp)
                elif self.position > 0: # Close Long
                    self._close_position(current_price, timestamp)
                    self._open_position('short', current_price, timestamp)
            
            # TP/SL Logic (High/Low Check)
            if self.position != 0:
                self._check_tpsl(current_row, timestamp)

        # Close any open position at the end
        if self.position != 0:
            self._close_position(self.df.iloc[-1]['close'], self.df.iloc[-1]['timestamp'])

    def _open_position(self, side, price, time):
        amount = (self.balance * 0.99) / price # Use 99% of balance
        fee = amount * price * config.TAKER_FEE_PCT
        
        if side == 'long':
            self.position = amount
        else:
            self.position = -amount
            
        self.entry_price = price
        self.balance -= fee
        logger.info(f"[{time}] OPEN {side.upper()} @ {price:.2f} | Fee: {fee:.4f}")

    def _close_position(self, price, time):
        if self.position == 0: return
        
        size = abs(self.position)
        value = size * price
        fee = value * config.TAKER_FEE_PCT
        
        pnl = 0
        if self.position > 0: # Long
            pnl = (price - self.entry_price) * size
        else: # Short
            pnl = (self.entry_price - price) * size
            
        self.balance += pnl - fee
        self.position = 0
        self.trades.append({'pnl': pnl - fee, 'time': time})
        logger.info(f"[{time}] CLOSE @ {price:.2f} | PnL: {pnl:.4f} | Fee: {fee:.4f} | Bal: {self.balance:.2f}")

    def _check_tpsl(self, row, time):
        # TP/SL check using High/Low for realistic simulation
        high = row['high']
        low = row['low']
        close = row['close']
        
        if self.position > 0: # Long
            tp_price = self.entry_price * (1 + config.TAKE_PROFIT_PCT)
            sl_price = self.entry_price * (1 - config.STOP_LOSS_PCT)
            
            # Check if SL hit first (conservative assumption: worst case)
            if low <= sl_price:
                logger.info("SL Hit")
                self._close_position(sl_price, time)
            elif high >= tp_price:
                logger.info("TP Hit")
                self._close_position(tp_price, time)
                
        elif self.position < 0: # Short
            tp_price = self.entry_price * (1 - config.TAKE_PROFIT_PCT)
            sl_price = self.entry_price * (1 + config.STOP_LOSS_PCT)
            
            # Check if SL hit first
            if high >= sl_price:
                logger.info("SL Hit")
                self._close_position(sl_price, time)
            elif low <= tp_price:
                logger.info("TP Hit")
                self._close_position(tp_price, time)

    def show_results(self):
        logger.info("-" * 30)
        logger.info("BACKTEST RESULTS")
        logger.info("-" * 30)
        logger.info(f"Final Balance: {self.balance:.2f}")
        logger.info(f"Total Return: {((self.balance - 1000)/1000)*100:.2f}%")
        logger.info(f"Total Trades: {len(self.trades)}")
        
        wins = [t for t in self.trades if t['pnl'] > 0]
        win_rate = (len(wins) / len(self.trades)) * 100 if self.trades else 0
        logger.info(f"Win Rate: {win_rate:.2f}%")

if __name__ == "__main__":
    # Example Usage
    bt = Backtester(symbol='BTC/USDT', timeframe='1m', strategy_name='mean_reversion')
    bt.fetch_data()
    bt.run()
    bt.show_results()

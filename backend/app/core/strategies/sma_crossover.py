import pandas as pd
from .base import Strategy

class SMACrossover(Strategy):
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
        
        # Calculate SMAs using pandas
        df['sma_short'] = df['close'].rolling(window=self.short_window).mean()
        df['sma_long'] = df['close'].rolling(window=self.long_window).mean()
        return df

    def check_signal(self, row):
        # We need previous row for crossover check, but check_signal receives only current row.
        # This is a limitation of the current row-based check_signal design for crossover strategies.
        # However, we can check if we are currently "above" or "below" and rely on state or 
        # simply check the condition "short > long" as a BUY signal (Trend Following) 
        # OR we need to pass 'previous_row' or the full dataframe index.
        
        # For the optimized backtester loop in backtest.py, we are iterating.
        # To support crossovers properly without state, we might need to change backtest.py 
        # to pass (current_row, prev_row) OR just check "Is Short > Long" (Golden Cross state).
        
        # Let's implement a simple state check:
        # BUY if Short > Long
        # SELL if Short < Long
        # This is not exactly "Crossover" (which happens only once), but "Trend Following".
        # To detect Crossover specifically in a stateless `check_signal`, we'd need history.
        
        # ALTERNATIVE: Backtester passes `i` and `df` to `check_signal`? No, that breaks abstraction.
        
        # WORKAROUND for Backtester:
        # The backtester loop in `backtest.py` iterates `i`.
        # We can't easily get prev_row inside `check_signal` if we only get `row`.
        
        # Let's stick to "Trend Following" logic for now which is robust for stateless:
        # If SMA_Short > SMA_Long -> BUY (or hold buy)
        # If SMA_Short < SMA_Long -> SELL (or hold sell)
        
        sma_short = row.get('sma_short')
        sma_long = row.get('sma_long')
        
        if pd.isna(sma_short) or pd.isna(sma_long):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        if sma_short > sma_long:
            signal = 'BUY'
            score = 2
        elif sma_short < sma_long:
            signal = 'SELL'
            score = 2
            
        details = {
            'sma_short': sma_short,
            'sma_long': sma_long,
            'sma': f"{sma_short:.2f}/{sma_long:.2f}"
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

    def generate_signal(self, df):
        if df is None or df.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        df = self.calculate_indicators(df)
        
        # For live trading (generate_signal), we HAVE the full dataframe, so we can do proper crossover check
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        if pd.isna(last_row['sma_short']) or pd.isna(last_row['sma_long']):
            return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        # Bullish crossover
        if prev_row['sma_short'] <= prev_row['sma_long'] and last_row['sma_short'] > last_row['sma_long']:
            signal = 'BUY'
            score = 2
        # Bearish crossover
        elif prev_row['sma_short'] >= prev_row['sma_long'] and last_row['sma_short'] < last_row['sma_long']:
            signal = 'SELL'
            score = 2
            
        details = {
            'sma_short': last_row['sma_short'],
            'sma_long': last_row['sma_long'],
            'sma': f"{last_row['sma_short']:.2f}/{last_row['sma_long']:.2f}"
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

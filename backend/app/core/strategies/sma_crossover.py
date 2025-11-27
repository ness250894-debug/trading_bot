import pandas as pd
from .base import Strategy

class SMACrossover(Strategy):
    def __init__(self, fast_period=10, slow_period=30):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
        
        # Calculate SMAs using pandas
        df['sma_short'] = df['close'].rolling(window=self.fast_period).mean()
        df['sma_long'] = df['close'].rolling(window=self.slow_period).mean()
        return df

    def check_signal(self, current_row, previous_row=None):
        if previous_row is None:
            # Fallback to trend following if no previous row
            return self._check_trend(current_row)

        sma_short_curr = current_row.get('sma_short')
        sma_long_curr = current_row.get('sma_long')
        sma_short_prev = previous_row.get('sma_short')
        sma_long_prev = previous_row.get('sma_long')
        
        if pd.isna(sma_short_curr) or pd.isna(sma_long_curr) or pd.isna(sma_short_prev) or pd.isna(sma_long_prev):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        # Bullish Crossover: Short crosses above Long
        if sma_short_prev <= sma_long_prev and sma_short_curr > sma_long_curr:
            signal = 'BUY'
            score = 2
        # Bearish Crossover: Short crosses below Long
        elif sma_short_prev >= sma_long_prev and sma_short_curr < sma_long_curr:
            signal = 'SELL'
            score = 2
            
        details = {
            'sma_short': sma_short_curr,
            'sma_long': sma_long_curr,
            'sma': f"{sma_short_curr:.2f}/{sma_long_curr:.2f}"
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

    def _check_trend(self, row):
        # Fallback method for stateless check (Trend Following)
        sma_short = row.get('sma_short')
        sma_long = row.get('sma_long')
        
        if pd.isna(sma_short) or pd.isna(sma_long):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        if sma_short > sma_long:
            signal = 'BUY'
            score = 1 # Lower score for trend following
        elif sma_short < sma_long:
            signal = 'SELL'
            score = 1
            
        return {
            'signal': signal,
            'score': score,
            'details': {'sma_short': sma_short, 'sma_long': sma_long}
        }

    def generate_signal(self, df):
        if df is None or df.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        df = self.calculate_indicators(df)
        
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        return self.check_signal(last_row, prev_row)

    def populate_buy_trend(self, df):
        # Vectorized Crossover Logic
        # Shift columns to get previous values
        df['sma_short_prev'] = df['sma_short'].shift(1)
        df['sma_long_prev'] = df['sma_long'].shift(1)
        
        df.loc[
            (df['sma_short_prev'] <= df['sma_long_prev']) &
            (df['sma_short'] > df['sma_long']),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df['sma_short_prev'] = df['sma_short'].shift(1)
        df['sma_long_prev'] = df['sma_long'].shift(1)
        
        df.loc[
            (df['sma_short_prev'] >= df['sma_long_prev']) &
            (df['sma_short'] < df['sma_long']),
            'sell'] = 1
        return df

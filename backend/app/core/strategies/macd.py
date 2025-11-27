import pandas as pd
from .base import Strategy

class MACDStrategy(Strategy):
    def __init__(self, fast=10, slow=21, signal=9, fast_period=None, slow_period=None, signal_period=None):
        # Map optimization params to class attributes if provided
        self.fast = fast_period if fast_period is not None else fast
        self.slow = slow_period if slow_period is not None else slow
        self.signal = signal_period if signal_period is not None else signal

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
        
        # Calculate MACD
        exp1 = df['close'].ewm(span=self.fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=self.signal, adjust=False).mean()
        
        df['macd'] = macd
        df['macd_signal'] = signal_line
        return df

    def check_signal(self, current_row, previous_row=None):
        if previous_row is None:
            # Fallback to trend following
            return self._check_trend(current_row)

        current_macd = current_row.get('macd')
        current_signal = current_row.get('macd_signal')
        prev_macd = previous_row.get('macd')
        prev_signal = previous_row.get('macd_signal')
        
        if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(prev_macd) or pd.isna(prev_signal):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        # Bullish Crossover
        if prev_macd < prev_signal and current_macd > current_signal:
            signal = 'BUY'
            score = 2
        # Bearish Crossover
        elif prev_macd > prev_signal and current_macd < current_signal:
            signal = 'SELL'
            score = 2
            
        details = {
            'macd': round(current_macd, 2),
            'macd_signal': round(current_signal, 2),
            'diff': round(current_macd - current_signal, 2)
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

    def _check_trend(self, row):
        macd = row.get('macd')
        signal_line = row.get('macd_signal')
        
        if pd.isna(macd) or pd.isna(signal_line):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        if macd > signal_line:
            signal = 'BUY'
            score = 1
        elif macd < signal_line:
            signal = 'SELL'
            score = 1
            
        return {
            'signal': signal,
            'score': score,
            'details': {'macd': macd, 'macd_signal': signal_line}
        }

    def generate_signal(self, dataframe):
        if dataframe is None or dataframe.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        df = self.calculate_indicators(dataframe)
        
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        return self.check_signal(last_row, prev_row)

    def populate_buy_trend(self, df):
        df['macd_prev'] = df['macd'].shift(1)
        df['signal_prev'] = df['macd_signal'].shift(1)
        
        df.loc[
            (df['macd_prev'] < df['signal_prev']) &
            (df['macd'] > df['macd_signal']),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df['macd_prev'] = df['macd'].shift(1)
        df['signal_prev'] = df['macd_signal'].shift(1)
        
        df.loc[
            (df['macd_prev'] > df['signal_prev']) &
            (df['macd'] < df['macd_signal']),
            'sell'] = 1
        return df

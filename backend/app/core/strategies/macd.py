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

    def check_signal(self, row):
        # Similar to SMA, we use Trend Following logic for stateless check
        # BUY if MACD > Signal
        # SELL if MACD < Signal
        
        macd = row.get('macd')
        signal_line = row.get('macd_signal')
        
        if pd.isna(macd) or pd.isna(signal_line):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        if macd > signal_line:
            signal = 'BUY'
            score = 2
        elif macd < signal_line:
            signal = 'SELL'
            score = 2
            
        details = {
            'macd': round(macd, 2),
            'macd_signal': round(signal_line, 2),
            'diff': round(macd - signal_line, 2)
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

    def generate_signal(self, dataframe):
        if dataframe is None or dataframe.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
        
        df = self.calculate_indicators(dataframe)
        
        # Check for crossover (Live Trading)
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
            
        current_macd = df.iloc[-1]['macd']
        current_signal = df.iloc[-1]['macd_signal']
        prev_macd = df.iloc[-2]['macd']
        prev_signal = df.iloc[-2]['macd_signal']
        
        # Crossover Logic
        signal = 'HOLD'
        score = 0
        
        if prev_macd < prev_signal and current_macd > current_signal:
            signal = 'BUY'
            score = 2
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

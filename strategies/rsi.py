import pandas as pd
from .base import Strategy

class RSIStrategy(Strategy):
    def __init__(self, period=14, overbought=65, oversold=35):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    def check_signal(self, row):
        current_rsi = row.get('rsi')
        
        if pd.isna(current_rsi):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        signal = 'HOLD'
        score = 0
        
        if current_rsi < self.oversold:
            signal = 'BUY'
            score = 2
        elif current_rsi > self.overbought:
            signal = 'SELL'
            score = 2
            
        details = {
            'rsi': round(current_rsi, 2)
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
        
        # Get last RSI value
        current_rsi = df.iloc[-1]['rsi']
        
        signal = 'HOLD'
        score = 0
        
        if current_rsi < self.oversold:
            signal = 'BUY'
            score = 2
        elif current_rsi > self.overbought:
            signal = 'SELL'
            score = 2
            
        details = {
            'rsi': round(current_rsi, 2)
        }
            
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

from .base import Strategy
import pandas as pd
import numpy as np

class Momentum(Strategy):
    def __init__(self, roc_period=10, rsi_period=14, rsi_min=50, rsi_max=70):
        self.roc_period = roc_period
        self.rsi_period = rsi_period
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
            
        # Calculate ROC (Rate of Change)
        df['roc'] = df['close'].pct_change(periods=self.roc_period) * 100
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df['rsi'] = rsi.fillna(50)
        return df

    def check_signal(self, current_row, previous_row=None):
        current_roc = current_row.get('roc', 0)
        current_rsi = current_row.get('rsi', 50)
        
        signal = 'HOLD'
        score = 0
        
        if pd.isna(current_roc) or pd.isna(current_rsi):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        # Buy Signal: Positive Momentum (ROC > 0) and RSI in bullish zone (but not overbought)
        if current_roc > 0 and current_rsi > self.rsi_min and current_rsi < self.rsi_max:
            signal = 'BUY'
            score = 3
        # Sell Signal: Negative Momentum
        elif current_roc < 0:
            signal = 'SELL'
            score = 2
            
        details = {
            'roc': round(current_roc, 2),
            'rsi': round(current_rsi, 2)
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
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        return self.check_signal(last_row, prev_row)

    def populate_buy_trend(self, df):
        df.loc[
            (df['roc'] > 0) &
            (df['rsi'] > self.rsi_min) &
            (df['rsi'] < self.rsi_max),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df.loc[
            (df['roc'] < 0),
            'sell'] = 1
        return df

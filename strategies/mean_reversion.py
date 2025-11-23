from strategies.base import Strategy
import pandas as pd
import numpy as np

class MeanReversion(Strategy):
    def __init__(self, bb_length=20, bb_std=2.0, rsi_length=14, rsi_buy=30, rsi_sell=70):
        self.bb_length = bb_length
        self.bb_std = bb_std
        self.rsi_length = rsi_length
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
            
        # Calculate Bollinger Bands
        sma = df['close'].rolling(window=self.bb_length).mean()
        std = df['close'].rolling(window=self.bb_length).std()
        
        df['bb_upper'] = sma + (std * self.bb_std)
        df['bb_lower'] = sma - (std * self.bb_std)
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        avg_gain = gain.rolling(window=self.rsi_length).mean()
        avg_loss = loss.rolling(window=self.rsi_length).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df['rsi'] = rsi.fillna(50)
        return df

    def check_signal(self, row):
        # Get values from row
        current_price = row['close']
        current_lower = row.get('bb_lower', 0)
        current_upper = row.get('bb_upper', 0)
        current_rsi = row.get('rsi', 50)
        
        signal = 'HOLD'
        score = 0
        
        if pd.isna(current_lower) or pd.isna(current_upper) or pd.isna(current_rsi):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        if current_price <= current_lower and current_rsi < self.rsi_buy:
            signal = 'BUY'
            score = 3
        elif current_price >= current_upper and current_rsi > self.rsi_sell:
            signal = 'SELL'
            score = 3
            
        details = {
            'bb_lower': round(current_lower, 2),
            'bb_upper': round(current_upper, 2),
            'rsi': round(current_rsi, 2),
            'price': current_price
        }
        
        return {
            'signal': signal,
            'score': score,
            'details': details
        }

    def generate_signal(self, df):
        if df is None or df.empty:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}

        # For backward compatibility / live trading
        df = self.calculate_indicators(df)
        last_row = df.iloc[-1]
        return self.check_signal(last_row)

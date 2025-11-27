from .base import Strategy
import pandas as pd
import numpy as np

class MeanReversion(Strategy):
    def __init__(self, bb_period=20, bb_std=2.0, rsi_period=14, rsi_oversold=30, rsi_overbought=70):
        # Map to internal naming for consistency
        self.bb_length = bb_period
        self.bb_std = bb_std
        self.rsi_length = rsi_period
        self.rsi_buy = rsi_oversold
        self.rsi_sell = rsi_overbought

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

    def check_signal(self, current_row, previous_row=None):
        # Get values from row
        current_price = current_row['close']
        current_lower = current_row.get('bb_lower', 0)
        current_upper = current_row.get('bb_upper', 0)
        current_rsi = current_row.get('rsi', 50)
        
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
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        return self.check_signal(last_row, prev_row)

    def populate_buy_trend(self, df):
        df.loc[
            (df['close'] < df['bb_lower']) &
            (df['rsi'] < self.rsi_buy),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df.loc[
            (df['close'] > df['bb_upper']) &
            (df['rsi'] > self.rsi_sell),
            'sell'] = 1
        return df

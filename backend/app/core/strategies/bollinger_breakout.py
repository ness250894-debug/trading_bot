from .base import Strategy
import pandas as pd
import numpy as np

class BollingerBreakout(Strategy):
    def __init__(self, bb_period=20, bb_std=2.0, volume_factor=1.5):
        self.bb_length = bb_period
        self.bb_std = bb_std
        self.volume_factor = volume_factor

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
            
        # Calculate Bollinger Bands
        sma = df['close'].rolling(window=self.bb_length).mean()
        std = df['close'].rolling(window=self.bb_length).std()
        
        df['bb_upper'] = sma + (std * self.bb_std)
        df['bb_lower'] = sma - (std * self.bb_std)
        df['bb_middle'] = sma
        
        # Volume Moving Average
        df['volume_ma'] = df['volume'].rolling(window=self.bb_length).mean()
        
        return df

    def check_signal(self, current_row, previous_row=None):
        current_price = current_row['close']
        current_upper = current_row.get('bb_upper', 0)
        current_middle = current_row.get('bb_middle', 0)
        current_volume = current_row.get('volume', 0)
        volume_ma = current_row.get('volume_ma', 0)
        
        signal = 'HOLD'
        score = 0
        
        if pd.isna(current_upper) or pd.isna(current_middle):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        # Buy Signal: Price breaks above upper band with volume
        if current_price > current_upper and current_volume > (volume_ma * self.volume_factor):
            signal = 'BUY'
            score = 3
        # Sell Signal: Price falls below middle band (Trend weakness)
        elif current_price < current_middle:
            signal = 'SELL'
            score = 2
            
        details = {
            'bb_upper': round(current_upper, 2),
            'bb_middle': round(current_middle, 2),
            'price': current_price,
            'volume_spike': round(current_volume / volume_ma, 2) if volume_ma > 0 else 0
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
            (df['close'] > df['bb_upper']) &
            (df['volume'] > df['volume_ma'] * self.volume_factor),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df.loc[
            (df['close'] < df['bb_middle']),
            'sell'] = 1
        return df

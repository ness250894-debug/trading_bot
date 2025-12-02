from .base import Strategy
import pandas as pd
import numpy as np

class DCADip(Strategy):
    def __init__(self, ema_long=200, ema_short=20):
        self.ema_long_period = ema_long
        self.ema_short_period = ema_short

    def calculate_indicators(self, df):
        if df is None or df.empty:
            return df
            
        # Calculate EMAs
        df['ema_long'] = df['close'].ewm(span=self.ema_long_period, adjust=False).mean()
        df['ema_short'] = df['close'].ewm(span=self.ema_short_period, adjust=False).mean()
        
        return df

    def check_signal(self, current_row, previous_row=None):
        current_price = current_row['close']
        ema_long = current_row.get('ema_long', 0)
        ema_short = current_row.get('ema_short', 0)
        
        signal = 'HOLD'
        score = 0
        
        if pd.isna(ema_long) or pd.isna(ema_short):
             return {'signal': 'HOLD', 'score': 0, 'details': {}}

        # Buy Signal: Trend is UP (Price > EMA200) AND Price is dipping (Price < EMA20)
        if current_price > ema_long and current_price < ema_short:
            signal = 'BUY'
            score = 3
        # Sell Signal: Trend Reversal (Price < EMA200)
        elif current_price < ema_long:
            signal = 'SELL'
            score = 3
            
        details = {
            'ema_long': round(ema_long, 2),
            'ema_short': round(ema_short, 2),
            'price': current_price,
            'trend': 'UP' if current_price > ema_long else 'DOWN'
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
            (df['close'] > df['ema_long']) &
            (df['close'] < df['ema_short']),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df.loc[
            (df['close'] < df['ema_long']),
            'sell'] = 1
        return df

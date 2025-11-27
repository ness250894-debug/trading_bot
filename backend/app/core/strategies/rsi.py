import pandas as pd
from .base import Strategy

class RSIStrategy(Strategy):
    def __init__(self, period=14, overbought=65, oversold=35, buy_threshold=None, sell_threshold=None):
        self.period = period
        # Map optimization params (buy_threshold/sell_threshold) to class attributes if provided
        self.overbought = sell_threshold if sell_threshold is not None else overbought
        self.oversold = buy_threshold if buy_threshold is not None else oversold

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

    def check_signal(self, current_row, previous_row=None):
        current_rsi = current_row.get('rsi')
        
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
        
        if len(df) < 2:
            return {'signal': 'HOLD', 'score': 0, 'details': {}}
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        return self.check_signal(last_row, prev_row)

    def populate_buy_trend(self, df):
        df.loc[
            (df['rsi'] < self.oversold),
            'buy'] = 1
        return df

    def populate_sell_trend(self, df):
        df.loc[
            (df['rsi'] > self.overbought),
            'sell'] = 1
        return df

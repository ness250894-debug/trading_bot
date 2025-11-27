from .sma_crossover import SMACrossover
from .rsi import RSIStrategy
from .macd import MACDStrategy

class CombinedStrategy:
    def __init__(self, **kwargs):
        # Extract params for each strategy with defaults
        sma_fast = kwargs.get('sma_fast', 10)
        sma_slow = kwargs.get('sma_slow', 30)
        
        rsi_period = kwargs.get('rsi_period', 14)
        rsi_overbought = kwargs.get('rsi_overbought', 65)
        rsi_oversold = kwargs.get('rsi_oversold', 35)
        
        macd_fast = kwargs.get('macd_fast', 10)
        macd_slow = kwargs.get('macd_slow', 21)
        macd_signal = kwargs.get('macd_signal', 9)

        self.sma = SMACrossover(fast_period=sma_fast, slow_period=sma_slow)
        self.rsi = RSIStrategy(period=rsi_period, overbought=rsi_overbought, oversold=rsi_oversold)
        self.macd = MACDStrategy(fast=macd_fast, slow=macd_slow, signal=macd_signal)

    def generate_signal(self, dataframe):
        """
        Returns a dictionary:
        {
            'signal': 'BUY' | 'SELL' | 'HOLD',
            'score': int (1-3),
            'details': { 'sma': ..., 'rsi': ..., 'macd': ... }
        }
        """
        sma_result = self.sma.generate_signal(dataframe)
        rsi_result = self.rsi.generate_signal(dataframe)
        macd_result = self.macd.generate_signal(dataframe)
        
        sma_signal = sma_result['signal']
        rsi_signal = rsi_result['signal']
        macd_signal = macd_result['signal']
        
        signals = [sma_signal, rsi_signal, macd_signal]
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        final_signal = 'HOLD'
        score = 0
        
        # Conflict Resolution: If both Buy and Sell exist, HOLD.
        if buy_count > 0 and sell_count > 0:
            final_signal = 'HOLD'
            score = 0
        elif buy_count > 0:
            final_signal = 'BUY'
            score = buy_count
        elif sell_count > 0:
            final_signal = 'SELL'
            score = sell_count
            
        return {
            'signal': final_signal,
            'score': score,
            'details': {
                'sma': sma_signal,
                'rsi': rsi_signal,
                'macd': macd_signal
            }
        }

    def populate_indicators(self, df):
        # Combined doesn't have its own indicators, but we need this method
        # to satisfy the interface if called directly.
        # However, sub-strategies populate their own.
        return df

    def populate_buy_trend(self, df):
        # SMA
        df_sma = df.copy()
        df_sma = self.sma.populate_indicators(df_sma)
        df_sma = self.sma.populate_buy_trend(df_sma)
        df['buy_sma'] = df_sma['buy'].fillna(0)
        
        # RSI
        df_rsi = df.copy()
        df_rsi = self.rsi.populate_indicators(df_rsi)
        df_rsi = self.rsi.populate_buy_trend(df_rsi)
        df['buy_rsi'] = df_rsi['buy'].fillna(0)
        
        # MACD
        df_macd = df.copy()
        df_macd = self.macd.populate_indicators(df_macd)
        df_macd = self.macd.populate_buy_trend(df_macd)
        df['buy_macd'] = df_macd['buy'].fillna(0)
        
        return df

    def populate_sell_trend(self, df):
        # SMA
        df_sma = df.copy()
        df_sma = self.sma.populate_indicators(df_sma)
        df_sma = self.sma.populate_sell_trend(df_sma)
        df['sell_sma'] = df_sma['sell'].fillna(0)
        
        # RSI
        df_rsi = df.copy()
        df_rsi = self.rsi.populate_indicators(df_rsi)
        df_rsi = self.rsi.populate_sell_trend(df_rsi)
        df['sell_rsi'] = df_rsi['sell'].fillna(0)
        
        # MACD
        df_macd = df.copy()
        df_macd = self.macd.populate_indicators(df_macd)
        df_macd = self.macd.populate_sell_trend(df_macd)
        df['sell_macd'] = df_macd['sell'].fillna(0)
        
        # Combine Logic
        # Buy Count
        df['buy_count'] = df['buy_sma'] + df['buy_rsi'] + df['buy_macd']
        
        # Sell Count
        df['sell_count'] = df['sell_sma'] + df['sell_rsi'] + df['sell_macd']
        
        # Final Buy: buy_count > 0 AND sell_count == 0
        df.loc[
            (df['buy_count'] > 0) & (df['sell_count'] == 0),
            'buy'] = 1
            
        # Final Sell: sell_count > 0 AND buy_count == 0
        df.loc[
            (df['sell_count'] > 0) & (df['buy_count'] == 0),
            'sell'] = 1
            
        return df

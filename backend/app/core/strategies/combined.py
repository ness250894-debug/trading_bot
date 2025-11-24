from .sma_crossover import SMACrossover
from .rsi import RSIStrategy
from .macd import MACDStrategy

class CombinedStrategy:
    def __init__(self):
        self.sma = SMACrossover(short_window=10, long_window=30)
        self.rsi = RSIStrategy(period=14, overbought=65, oversold=35)
        self.macd = MACDStrategy(fast=10, slow=21, signal=9)

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

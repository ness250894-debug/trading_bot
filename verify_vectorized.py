import logging
import pandas as pd
from backend.app.core.vectorized_backtest import VectorizedBacktester
from backend.app.core.backtest import Backtester
from backend.app.core.strategies.mean_reversion import MeanReversion

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify():
    # 1. Create Mock Data
    data = {
        'timestamp': pd.date_range(start='2023-01-01', periods=500, freq='1h'),
        'open': [100] * 500,
        'high': [105] * 500,
        'low': [95] * 500,
        'close': [100] * 500,
        'volume': [1000] * 500
    }
    df = pd.DataFrame(data)
    
    # Simulate price movement for Mean Reversion
    # Drop price to trigger buy, raise to trigger sell
    df.loc[100:110, 'close'] = 90 # Buy Zone (Low BB)
    df.loc[100:110, 'low'] = 85
    
    df.loc[120:130, 'close'] = 110 # Sell Zone (High BB)
    df.loc[120:130, 'high'] = 115
    
    # 2. Run Old Backtester
    print("\n--- Running Old Backtester ---")
    old_bt = Backtester('BTC/USDT', '1h', MeanReversion(), data=df.copy())
    old_bt.run()
    old_bt.show_results()
    
    # 3. Run New Vectorized Backtester
    print("\n--- Running New Vectorized Backtester ---")
    new_bt = VectorizedBacktester('BTC/USDT', '1h', MeanReversion(), data=df.copy())
    new_bt.run()
    new_bt.show_results()

if __name__ == "__main__":
    verify()

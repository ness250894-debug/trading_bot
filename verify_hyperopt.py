import logging
import pandas as pd
import optuna
from backend.app.core.hyperopt import Hyperopt

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify():
    # 1. Create Mock Data
    data = {
        'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='1h'),
        'open': [100] * 1000,
        'high': [105] * 1000,
        'low': [95] * 1000,
        'close': [100] * 1000,
        'volume': [1000] * 1000
    }
    df = pd.DataFrame(data)
    
    # Simulate price movement for Mean Reversion
    # We create a pattern that a specific RSI/BB combo should catch
    # e.g. Dip to 90 when RSI is low
    
    for i in range(100, 900, 50):
        df.loc[i:i+5, 'close'] = 90 # Dip
        df.loc[i:i+5, 'low'] = 85
    
    for i in range(120, 920, 50):
        df.loc[i:i+5, 'close'] = 110 # Peak
        df.loc[i:i+5, 'high'] = 115

    # 2. Run Hyperopt
    print("\n--- Running Hyperopt ---")
    optimizer = Hyperopt('BTC/USDT', '1h', df)
    best_params, best_value = optimizer.optimize(n_trials=10) # 10 trials for speed
    
    print(f"\nBest Return: {best_value:.2f}%")
    print(f"Best Params: {best_params}")

if __name__ == "__main__":
    verify()

import itertools
import pandas as pd
import logging
from .backtest import Backtester

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Optimizer")

class Optimizer:
    def __init__(self, symbol, timeframe, strategy_class, data):
        self.symbol = symbol
        self.timeframe = timeframe
        self.strategy_class = strategy_class
        self.data = data
        self.results = []

    async def optimize(self, param_ranges, progress_callback=None):
        """
        Runs a grid search over the parameter ranges.
        param_ranges: dict of parameter names and their list of values to test.
        Example: {'short_window': range(5, 15), 'long_window': range(20, 40)}
        """
        keys = param_ranges.keys()
        values = param_ranges.values()
        combinations = list(itertools.product(*values))
        
        total_combinations = len(combinations)
        logger.info(f"Starting optimization with {total_combinations} combinations...")
        
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            
            # Instantiate strategy with current params
            try:
                strategy = self.strategy_class(**params)
            except Exception as e:
                logger.error(f"Failed to instantiate strategy with params {params}: {e}")
                continue
            
            # Run Backtest
            # We pass the pre-fetched data to avoid re-fetching
            bt = Backtester(self.symbol, self.timeframe, strategy, data=self.data.copy())
            bt.run()
            
            # Collect Metrics
            total_return = ((bt.balance - 1000) / 1000) * 100
            wins = [t for t in bt.trades if t['pnl'] > 0]
            win_rate = (len(wins) / len(bt.trades)) * 100 if bt.trades else 0
            
            result = {
                'params': params,
                'return': total_return,
                'win_rate': win_rate,
                'trades': len(bt.trades),
                'final_balance': bt.balance
            }
            self.results.append(result)
            
            if (i + 1) % 1 == 0:
                if progress_callback:
                    await progress_callback(i + 1, total_combinations)
                logger.info(f"Processed {i + 1}/{total_combinations} combinations.")
                
        # Convert to DataFrame
        results_df = pd.DataFrame(self.results)
        if not results_df.empty:
            results_df = results_df.sort_values(by='return', ascending=False)
            
        return results_df

import optuna
import logging
from .vectorized_backtest import VectorizedBacktester
from .strategies.mean_reversion import MeanReversion

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Hyperopt")

# Suppress Optuna logging to avoid clutter
optuna.logging.set_verbosity(optuna.logging.WARNING)

class Hyperopt:
    def __init__(self, symbol, timeframe, data):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = data

    def optimize(self, param_ranges, strategy_class, n_trials=50, progress_callback=None):
        logger.info(f"Starting Hyperopt with {n_trials} trials...")

        def objective(trial):
            # 1. Suggest Parameters Dynamically
            params = {}
            for param_name, ranges in param_ranges.items():
                # ranges is expected to be [min, max] or [min, max, step]
                if len(ranges) == 2:
                    low, high = ranges
                    if isinstance(low, int) and isinstance(high, int):
                        params[param_name] = trial.suggest_int(param_name, low, high)
                    else:
                        params[param_name] = trial.suggest_float(param_name, low, high)
                elif len(ranges) == 3:
                    low, high, step = ranges
                    if isinstance(step, int):
                         params[param_name] = trial.suggest_int(param_name, low, high, step=step)
                    else:
                         params[param_name] = trial.suggest_float(param_name, low, high, step=step)

            # 2. Instantiate Strategy
            try:
                strategy = strategy_class(**params)
            except Exception as e:
                # If invalid params are generated (e.g. rsi_buy > rsi_sell), prune trial
                raise optuna.TrialPruned()

            # 3. Run Backtest
            # We use the vectorized backtester for speed
            bt = VectorizedBacktester(self.symbol, self.timeframe, strategy, data=self.data.copy())
            bt.run()

            # 4. Return Metric (Minimize or Maximize)
            # Optuna minimizes by default if direction not set, but we set direction='maximize' below
            # We want to maximize Total Return
            
            # Calculate Metrics
            total_return = ((bt.balance - 1000) / 1000) * 100
            trades_count = len(bt.trades)
            wins = [t for t in bt.trades if t['pnl'] > 0]
            win_rate = (len(wins) / trades_count) * 100 if trades_count > 0 else 0
            
            # Store metrics in trial for retrieval later
            trial.set_user_attr("win_rate", win_rate)
            trial.set_user_attr("trades", trades_count)
            trial.set_user_attr("final_balance", bt.balance)
            
            # Optional: Penalize low trade count to avoid overfitting on 1 lucky trade
            # Reduced penalty to allow seeing results
            if trades_count < 2:
                return -100 

            return total_return
        
        # Create Study
        study = optuna.create_study(direction='maximize')
        
        # Optional: Add progress callback
        if progress_callback:
            for i in range(n_trials):
                study.optimize(objective, n_trials=1)
                best_trial = study.best_trial
                
                if progress_callback:
                    progress_callback(i + 1, n_trials, {
                        "best_return": best_trial.value,
                        "best_params": best_trial.params
                    })
        else:
            study.optimize(objective, n_trials=n_trials)

        # Log Results
        logger.info("Hyperopt Complete!")
        logger.info(f"Best Return: {study.best_value:.2f}%")
        logger.info(f"Best Params: {study.best_params}")
        
        # Store results for access
        trials_df = study.trials_dataframe()
        
        # Clean up column names
        rename_map = {'value': 'return'}
        for col in trials_df.columns:
            if col.startswith('params_'):
                rename_map[col] = col.replace('params_', '')
            elif col.startswith('user_attrs_'):
                rename_map[col] = col.replace('user_attrs_', '')
        
        trials_df = trials_df.rename(columns=rename_map)
        
        # Ensure JSON serializable types
        if 'duration' in trials_df.columns:
            trials_df['duration'] = trials_df['duration'].dt.total_seconds()
            
        if 'datetime_start' in trials_df.columns:
            trials_df['datetime_start'] = trials_df['datetime_start'].astype(str)
            
        if 'datetime_complete' in trials_df.columns:
            trials_df['datetime_complete'] = trials_df['datetime_complete'].astype(str)
            
        # Fill NaNs
        trials_df = trials_df.fillna(0)
        
        return trials_df

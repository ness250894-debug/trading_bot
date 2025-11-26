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
            
            # Calculate Total Return %
            total_return = ((bt.balance - 1000) / 1000) * 100
            
            # Optional: Penalize low trade count to avoid overfitting on 1 lucky trade
            if len(bt.trades) < 5:
                return -100 # Heavy penalty

            return total_return

        # Create Study
        study = optuna.create_study(direction='maximize')
        
        # Optional: Add progress callback
        if progress_callback:
            # Optuna doesn't support async callbacks directly in optimize, 
            # but we can wrap the objective or use a callback class.
            # For simplicity, we'll just run it and maybe report progress if we iterate manually.
            # But study.optimize is blocking. 
            # To support progress updates, we can loop n_trials times.
            for i in range(n_trials):
                study.optimize(objective, n_trials=1)
                best_trial = study.best_trial
                
                # Report progress
                import asyncio
                if asyncio.iscoroutinefunction(progress_callback):
                    # We can't await here easily if this is synchronous.
                    # But the caller (websocket handler) is async.
                    # We might need to make optimize async or run in thread.
                    # For now, let's assume optimize is called in a thread or we just don't await.
                    # Actually, since we are in a thread (job manager), we can't await async callback easily 
                    # unless we pass an event loop or use run_coroutine_threadsafe.
                    pass
                    
                # Let's just rely on the caller to handle async/thread stuff.
                # If we want to support progress, we should probably make this a generator or accept a sync callback.
                # The JobManager expects a sync function that calls an async callback? 
                # No, JobManager runs in a thread, so it can call sync callbacks.
                
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
        self.results = [] # We could populate this with all trials if needed
        # For now, let's just return a dataframe of all trials
        trials_df = study.trials_dataframe()
        # Rename columns to match expected output
        # 'params_bb_length' -> 'bb_length', 'value' -> 'return'
        
        # Clean up column names
        rename_map = {'value': 'return'}
        for col in trials_df.columns:
            if col.startswith('params_'):
                rename_map[col] = col.replace('params_', '')
        
        trials_df = trials_df.rename(columns=rename_map)
        
        # Add win_rate (not tracked by Optuna directly unless we return multiple objectives)
        # For now, we'll just return what we have. 
        # To get win_rate, we'd need to store it in user_attrs during objective.
        
        return trials_df

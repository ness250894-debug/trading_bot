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

    def optimize(self, n_trials=50):
        logger.info(f"Starting Hyperopt with {n_trials} trials...")

        def objective(trial):
            # 1. Suggest Parameters
            # These ranges should be adapted based on the strategy
            bb_length = trial.suggest_int('bb_length', 10, 50)
            bb_std = trial.suggest_float('bb_std', 1.0, 3.0, step=0.1)
            rsi_length = trial.suggest_int('rsi_length', 5, 30)
            rsi_buy = trial.suggest_int('rsi_buy', 10, 40)
            rsi_sell = trial.suggest_int('rsi_sell', 60, 90)

            # 2. Instantiate Strategy
            strategy = MeanReversion(
                bb_length=bb_length,
                bb_std=bb_std,
                rsi_length=rsi_length,
                rsi_buy=rsi_buy,
                rsi_sell=rsi_sell
            )

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
        study.optimize(objective, n_trials=n_trials)

        # Log Results
        logger.info("Hyperopt Complete!")
        logger.info(f"Best Return: {study.best_value:.2f}%")
        logger.info(f"Best Params: {study.best_params}")

        return study.best_params, study.best_value

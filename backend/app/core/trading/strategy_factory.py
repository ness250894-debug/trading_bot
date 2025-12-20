"""
Strategy Factory Module

Creates strategy instances based on strategy name and parameters.
Extracted from bot.py for better modularity and testability.
"""
import logging

logger = logging.getLogger("TradingBot")


def create_strategy(strategy_name: str, strategy_params: dict, user_id: int = None):
    """
    Factory function to create strategy instances.
    
    Args:
        strategy_name: Name of the strategy
        strategy_params: Strategy parameters
        user_id: Optional user ID for logging
    
    Returns:
        Strategy instance
    """
    # Define valid parameters for each strategy
    strategy_param_map = {
        'mean_reversion': ['bb_period', 'bb_std', 'rsi_period', 'rsi_oversold', 'rsi_overbought'],
        'sma_crossover': ['fast_period', 'slow_period'],
        'macd': ['fast', 'slow', 'signal', 'fast_period', 'slow_period', 'signal_period'],
        'rsi': ['period', 'overbought', 'oversold', 'buy_threshold', 'sell_threshold'],
        'bollinger_breakout': ['bb_period', 'bb_std', 'volume_factor'],
        'momentum': ['roc_period', 'rsi_period', 'rsi_min', 'rsi_max'],
        'dca_dip': ['ema_long', 'ema_short'],
        'combined': []  # Combined accepts any kwargs
    }
    
    # Filter parameters to only include valid ones for the selected strategy
    valid_params = strategy_param_map.get(strategy_name, [])
    if valid_params:  # If not combined strategy
        filtered_params = {k: v for k, v in strategy_params.items() if k in valid_params}
        logger.info(f"Filtered params for {strategy_name}: {filtered_params}")
    else:
        filtered_params = strategy_params  # Combined strategy accepts all
    
    # Import and instantiate the appropriate strategy
    if strategy_name == 'mean_reversion':
        from ..strategies.mean_reversion import MeanReversion
        return MeanReversion(**filtered_params)
    elif strategy_name == 'sma_crossover':
        from ..strategies.sma_crossover import SMACrossover
        return SMACrossover(**filtered_params)
    elif strategy_name == 'combined':
        from ..strategies.combined import CombinedStrategy
        return CombinedStrategy(**filtered_params)
    elif strategy_name == 'macd':
        from ..strategies.macd import MACDStrategy
        return MACDStrategy(**filtered_params)
    elif strategy_name == 'rsi':
        from ..strategies.rsi import RSIStrategy
        return RSIStrategy(**filtered_params)
    elif strategy_name == 'bollinger_breakout':
        from ..strategies.bollinger_breakout import BollingerBreakout
        return BollingerBreakout(**filtered_params)
    elif strategy_name == 'momentum':
        from ..strategies.momentum import Momentum
        return Momentum(**filtered_params)
    elif strategy_name == 'dca_dip':
        from ..strategies.dca_dip import DCADip
        return DCADip(**filtered_params)
    else:
        user_msg = f" for user {user_id}" if user_id else ""
        logger.warning(f"Unknown strategy '{strategy_name}'{user_msg}. Using Mean Reversion.")
        from ..strategies.mean_reversion import MeanReversion
        return MeanReversion(**filtered_params)

import pytest
from app.core.trading.strategy_factory import create_strategy
from app.core.strategies.mean_reversion import MeanReversion
from app.core.strategies.sma_crossover import SMACrossover
from app.core.strategies.combined import CombinedStrategy
from app.core.strategies.momentum import Momentum

class TestStrategyFactory:
    def test_create_mean_reversion(self):
        params = {'bb_period': 20, 'bb_std': 2.0}
        strategy = create_strategy('mean_reversion', params)
        assert isinstance(strategy, MeanReversion)
        assert strategy.bb_length == 20
        assert strategy.bb_std == 2.0

    def test_create_sma_crossover(self):
        params = {'fast_period': 10, 'slow_period': 50}
        strategy = create_strategy('sma_crossover', params)
        assert isinstance(strategy, SMACrossover)
        assert strategy.fast_period == 10
        assert strategy.slow_period == 50

    def test_create_combined_strategy(self):
        params = {'strategies': ['mean_reversion', 'momentum']}
        strategy = create_strategy('combined', params)
        # CombinedStrategy initialization might differ, checking class type mainly
        assert isinstance(strategy, CombinedStrategy)

    def test_unknown_strategy_fallback(self):
        """Test that unknown strategy falls back to MeanReversion"""
        strategy = create_strategy('unknown_strategy_xyz', {})
        assert isinstance(strategy, MeanReversion)

    def test_parameter_filtering(self):
        """Test that extra parameters are filtered out for specific strategies"""
        # Mean Reversion only takes specific params. 'invalid_param' should be ignored.
        # If it wasn't ignored, MeanReversion.__init__ would likely raise TypeError (unexpected argument)
        params = {'bb_period': 20, 'bb_std': 2.0, 'invalid_param': 123}
        strategy = create_strategy('mean_reversion', params)
        assert isinstance(strategy, MeanReversion)
        # No error means filtering worked

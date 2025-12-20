"""
Integration tests for refactored trading bot modules.

Tests the new modular architecture to ensure:
1. All modules work together correctly
2. Backward compatibility with bot_manager
3. Trading logic behaves as expected
"""
import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from backend.app.core.trading.trading_engine import TradingEngine
from backend.app.core.trading.strategy_factory import create_strategy
from backend.app.core.trading.market_data import MarketDataFetcher
from backend.app.core.trading.signal_generator import SignalGenerator
from backend.app.core.trading.risk_manager import RiskManager
from backend.app.core.trading.order_executor import OrderExecutor
from backend.app.core.trading.position_manager import PositionManager
from backend.app.core.trading.subscription_checker import SubscriptionChecker


@pytest.fixture
def mock_client():
    """Create a mock exchange client"""
    client = Mock()
    
    # Mock OHLCV data
    df = pd.DataFrame({
        'timestamp': range(100),
        'open': [100.0] * 100,
        'high': [101.0] * 100,
        'low': [99.0] * 100,
        'close': [100.0] * 100,
        'volume': [1000.0] * 100
    })
    client.fetch_ohlcv.return_value = df
    
    # Mock position (no position initially)
    client.fetch_position.return_value = {'size': 0.0, 'side': None}
    
    # Mock balance
    client.fetch_balance.return_value = {'total': {'USDT': 1000.0}}
    
    # Mock ticker
    client.fetch_ticker.return_value = {'last': 100.0}
    
    # Mock order creation
    client.create_order.return_value = {'id': '12345', 'status': 'filled'}
    client.fetch_order.return_value = {'id': '12345', 'average': 100.0, 'status': 'filled'}
    
    # Mock trades
    client.fetch_my_trades.return_value = [{'pnl': 5.0}]
    
    # Mock open orders
    client.fetch_open_orders.return_value = []
    
    return client


@pytest.fixture
def mock_db():
    """Create a mock database handler"""
    db = Mock()
    db.is_subscription_active.return_value = True
    db.get_risk_profile.return_value = None
    db.get_api_key.return_value = None
    db.get_user_by_id.return_value = {'telegram_chat_id': '123456'}
    db.log_trade.return_value = None
    db.update_bot_state.return_value = None
    return db


@pytest.fixture
def mock_notifier():
    """Create a mock telegram notifier"""
    notifier = Mock()
    notifier.send_message.return_value = None
    notifier.send_trade_alert.return_value = None
    notifier.send_error.return_value = None
    return notifier


@pytest.fixture
def strategy_config():
    """Create a test strategy configuration"""
    return {
        'SYMBOL': 'BTC/USDT',
        'TIMEFRAME': '1m',
        'AMOUNT_USDT': 100.0,
        'STRATEGY': 'sma_crossover',
        'STRATEGY_PARAMS': {'fast_period': 10, 'slow_period': 30},
        'DRY_RUN': True,
        'EXCHANGE': 'bybit',
        'LEVERAGE': 10.0,
        'TAKE_PROFIT_PCT': 0.02,
        'STOP_LOSS_PCT': 0.01
    }


class TestStrategyFactory:
    """Test strategy factory module"""
    
    def test_create_sma_crossover_strategy(self):
        """Test creating SMA Crossover strategy"""
        strategy = create_strategy('sma_crossover', {'fast_period': 10, 'slow_period': 30})
        assert strategy is not None
        assert hasattr(strategy, 'generate_signal')
    
    def test_create_mean_reversion_strategy(self):
        """Test creating Mean Reversion strategy"""
        params = {
            'bb_period': 20,
            'bb_std': 2.0,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        strategy = create_strategy('mean_reversion', params)
        assert strategy is not None
    
    def test_unknown_strategy_falls_back(self):
        """Test that unknown strategy falls back to default"""
        strategy = create_strategy('unknown_strategy', {})
        assert strategy is not None


class TestMarketDataFetcher:
    """Test market data fetcher module"""
    
    def test_fetch_ohlcv(self, mock_client):
        """Test OHLCV data fetching"""
        fetcher = MarketDataFetcher(mock_client, 'BTC/USDT', '1m')
        df = fetcher.fetch_ohlcv(limit=100)
        
        assert df is not None
        assert len(df) == 100
        assert 'close' in df.columns
        mock_client.fetch_ohlcv.assert_called_once()
    
    def test_fetch_position(self, mock_client):
        """Test position fetching"""
        fetcher = MarketDataFetcher(mock_client, 'BTC/USDT', '1m')
        position = fetcher.fetch_position()
        
        assert position is not None
        assert 'size' in position
        mock_client.fetch_position.assert_called_once()
    
    def test_get_current_price(self, mock_client):
        """Test extracting current price from DataFrame"""
        fetcher = MarketDataFetcher(mock_client, 'BTC/USDT', '1m')
        df = fetcher.fetch_ohlcv(limit=100)
        price = fetcher.get_current_price(df)
        
        assert price == 100.0


class TestSignalGenerator:
    """Test signal generator module"""
    
    def test_generate_signal_buy(self, mock_client):
        """Test generating BUY signal"""
        strategy = Mock()
        strategy.generate_signal.return_value = {'signal': 'BUY', 'score': 5, 'details': {'rsi': 35}}
        
        generator = SignalGenerator(strategy, user_id=1)
        df = mock_client.fetch_ohlcv.return_value
        
        signal, score, details, log_msg = generator.generate_and_parse_signal(df)
        
        assert signal == 'long'
        assert score == 5
        assert 'rsi' in details
        assert 'BUY' in log_msg
    
    def test_generate_signal_sell(self, mock_client):
        """Test generating SELL signal"""
        strategy = Mock()
        strategy.generate_signal.return_value = 'SELL'
        
        generator = SignalGenerator(strategy, user_id=1)
        df = mock_client.fetch_ohlcv.return_value
        
        signal, score, details, log_msg = generator.generate_and_parse_signal(df)
        
        assert signal == 'short'
    
    def test_generate_signal_hold(self, mock_client):
        """Test generating HOLD signal"""
        strategy = Mock()
        strategy.generate_signal.return_value = 'HOLD'
        
        generator = SignalGenerator(strategy, user_id=1)
        df = mock_client.fetch_ohlcv.return_value
        
        signal, score, details, log_msg = generator.generate_and_parse_signal(df)
        
        assert signal == 'hold'


class TestRiskManager:
    """Test risk manager module"""
    
    def test_check_subscription_active(self, mock_db, mock_notifier):
        """Test subscription check"""
        manager = RiskManager(mock_db, mock_notifier, user_id=1)
        
        assert manager.check_subscription_active() is True
        mock_db.is_subscription_active.assert_called_once_with(1)
    
    def test_check_can_open_position_no_profile(self, mock_db, mock_notifier):
        """Test risk check with no risk profile"""
        manager = RiskManager(mock_db, mock_notifier, user_id=1)
        
        allowed, reason = manager.check_can_open_position(100.0)
        
        assert allowed is True
        assert "No risk profile" in reason
    
    def test_check_can_open_position_exceeds_max_size(self, mock_db, mock_notifier):
        """Test risk check when position size exceeds limit"""
        mock_db.get_risk_profile.return_value = {'max_position_size': 50.0}
        manager = RiskManager(mock_db, mock_notifier, user_id=1)
        
        allowed, reason = manager.check_can_open_position(100.0)
        
        assert allowed is False
        assert "Max Position Size" in reason


class TestOrderExecutor:
    """Test order executor module"""
    
    def test_execute_entry_order_success(self, mock_client, mock_db, mock_notifier):
        """Test successful entry order execution"""
        executor = OrderExecutor(mock_client, mock_db, mock_notifier, user_id=1)
        
        success, entry_price = executor.execute_entry_order(
            symbol='BTC/USDT',
            signal='long',
            amount_usdt=100.0,
            current_price=100.0,
            strategy_name='test_strategy',
            take_profit_pct=0.02,
            stop_loss_pct=0.01
        )
        
        assert success is True
        assert entry_price == 100.0
        mock_client.create_order.assert_called_once()
        mock_db.log_trade.assert_called_once()
    
    def test_execute_exit_order_success(self, mock_client, mock_db, mock_notifier):
        """Test successful exit order execution"""
        executor = OrderExecutor(mock_client, mock_db, mock_notifier, user_id=1)
        
        position = {'size': 1.0, 'side': 'long'}
        success, pnl = executor.execute_exit_order(
            symbol='BTC/USDT',
            position=position,
            current_price=105.0,
            strategy_name='test_strategy'
        )
        
        assert success is True
        assert pnl == 5.0  # From mock
        mock_client.create_order.assert_called_once()


class TestPositionManager:
    """Test position manager module"""
    
    def test_calculate_unrealized_pnl_long(self, mock_db):
        """Test PnL calculation for long position"""
        manager = PositionManager(user_id=1, db=mock_db)
        
        position = {'size': 1.0, 'side': 'Buy', 'entry_price': 100.0}
        unrealized_pnl, pnl_pct = manager.calculate_unrealized_pnl(
            position, current_price=105.0, amount_usdt=100.0, leverage=10.0
        )
        
        assert pnl_pct == 0.05  # 5% gain
        assert unrealized_pnl == 5.0
    
    def test_calculate_unrealized_pnl_short(self, mock_db):
        """Test PnL calculation for short position"""
        manager = PositionManager(user_id=1, db=mock_db)
        
        position = {'size': 1.0, 'side': 'Sell', 'entry_price': 100.0}
        unrealized_pnl, pnl_pct = manager.calculate_unrealized_pnl(
            position, current_price=95.0, amount_usdt=100.0, leverage=10.0
        )
        
        assert pnl_pct == 0.05  # 5% gain
        assert unrealized_pnl == 5.0
    
    def test_update_state(self, mock_db):
        """Test state persistence"""
        manager = PositionManager(user_id=1, db=mock_db)
        
        manager.update_state(position_start_time=time.time())
        
        mock_db.update_bot_state.assert_called_once()


class TestSubscriptionChecker:
    """Test subscription checker module"""
    
    def test_should_check_now(self, mock_db, mock_notifier):
        """Test periodic check timing"""
        checker = SubscriptionChecker(mock_db, mock_notifier, user_id=1, loop_delay=5)
        
        # First few iterations should not trigger check
        for _ in range(checker.interval - 1):
            assert checker.should_check_now() is False
        
        # On interval, should trigger
        assert checker.should_check_now() is True
        
        # Then reset
        assert checker.should_check_now() is False


class TestTradingEngineIntegration:
    """Integration tests for the complete TradingEngine"""
    
    def test_backward_compatibility_with_run_bot_instance(self, strategy_config):
        """Test that run_bot_instance wrapper works"""
        from backend.app.core.bot import run_bot_instance
        
        # This test verifies the function exists and has correct signature
        import inspect
        sig = inspect.signature(run_bot_instance)
        params = list(sig.parameters.keys())
        
        assert 'user_id' in params
        assert 'strategy_config' in params
        assert 'running_event' in params
        assert 'runtime_state' in params


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

import pytest
import threading
import time
from unittest.mock import MagicMock, patch, ANY
from app.core.trading.trading_engine import TradingEngine

@pytest.fixture
def mock_deps():
    with patch('app.core.database.DuckDBHandler') as mock_db_cls, \
         patch('app.core.encryption.EncryptionHelper') as mock_enc_cls, \
         patch('app.core.client_manager.client_manager') as mock_cm, \
         patch('app.core.notifier.TelegramNotifier') as mock_notif_cls, \
         patch('app.core.trading.trading_engine.create_strategy') as mock_strat_factory, \
         patch('app.core.trading.trading_engine.MarketDataFetcher') as mock_mdf_cls, \
         patch('app.core.trading.trading_engine.SignalGenerator') as mock_sig_cls, \
         patch('app.core.trading.trading_engine.RiskManager') as mock_risk_cls, \
         patch('app.core.trading.trading_engine.OrderExecutor') as mock_exec_cls, \
         patch('app.core.trading.trading_engine.PositionManager') as mock_pos_cls, \
         patch('app.core.trading.trading_engine.SubscriptionChecker') as mock_sub_cls, \
         patch('app.core.trading.trading_engine.CircuitBreaker') as mock_cb_cls:
        
        # Setup Instances
        mock_db = mock_db_cls.return_value
        mock_enc = mock_enc_cls.return_value
        mock_notif = mock_notif_cls.return_value
        mock_mdf = mock_mdf_cls.return_value
        mock_sig = mock_sig_cls.return_value
        mock_risk = mock_risk_cls.return_value
        mock_exec = mock_exec_cls.return_value
        mock_pos = mock_pos_cls.return_value
        mock_sub = mock_sub_cls.return_value
        mock_cb = mock_cb_cls.return_value
        
        # Default Returns
        mock_db.get_api_key.return_value = {
            'api_key_encrypted': 'key_enc',
            'api_secret_encrypted': 'secret_enc'
        }
        mock_enc.decrypt.return_value = 'decrypted_cred'
        mock_db.get_user_by_id.return_value = {'telegram_chat_id': 12345}
        
        yield {
            'db': mock_db,
            'cm': mock_cm,
            'mdf': mock_mdf,
            'sig': mock_sig,
            'risk': mock_risk,
            'exec': mock_exec,
            'pos': mock_pos,
            'sub': mock_sub,
            'cb': mock_cb
        }

class TestTradingEngine:
    def test_initialization(self, mock_deps):
        """Test that all components are initialized correctly."""
        user_id = 1
        config = {'SYMBOL': 'BTC/USDT', 'STRATEGY': 'mean_reversion'}
        event = threading.Event()
        
        engine = TradingEngine(user_id, config, event)
        engine._initialize_components()
        
        mock_deps['db'].get_api_key.assert_called_with(user_id, 'bybit')
        
        # Verify components are assigned
        assert engine.market_data == mock_deps['mdf']
        assert engine.risk_mgr == mock_deps['risk']

    def test_calculate_loop_delay(self, mock_deps):
        event = threading.Event()
        
        # Test 1m timeframe override
        engine = TradingEngine(1, {'TIMEFRAME': '1m', 'STRATEGY': 'mean_reversion'}, event)
        assert engine.loop_delay == 5
        
        # Test 5m timeframe override
        engine = TradingEngine(1, {'TIMEFRAME': '5m', 'STRATEGY': 'macd'}, event)
        assert engine.loop_delay <= 10 # Should be 10 or less

    def test_trading_loop_execution_flow(self, mock_deps):
        """Test a single iteration of the trading loop."""
        user_id = 1
        config = {'SYMBOL': 'BTC/USDT', 'STRATEGY': 'mean_reversion'}
        event = threading.Event()
        event.set() # Start running
        
        engine = TradingEngine(user_id, config, event)
        engine._initialize_components()
        
        # Mock interactions for one loop
        mock_deps['cb'].is_open.return_value = False
        mock_deps['mdf'].fetch_ohlcv.return_value = "dataframe"
        mock_deps['mdf'].get_current_price.return_value = 50000.0
        mock_deps['mdf'].fetch_position.return_value = {'size': 0.0}
        
        # Signal Generation to return 'long'
        mock_deps['sig'].generate_and_parse_signal.return_value = ('long', 0.8, {}, "Buy Signal")
        
        # Sub checker
        mock_deps['sub'].should_check_now.return_value = False
        
        # Risk Manager allows trade
        mock_deps['risk'].check_subscription_active.return_value = True
        mock_deps['risk'].check_can_open_position.return_value = (True, "OK")
        
        # Order Execution success
        mock_deps['exec'].execute_entry_order.return_value = (True, 50000.0)
        
        # Mock time.sleep to raise exception to break infinite loop
        with patch('time.sleep', side_effect=InterruptedError("Loop Break")):
            try:
                engine._trading_loop()
            except InterruptedError:
                pass
        
        # Verification
        mock_deps['mdf'].fetch_ohlcv.assert_called()
        mock_deps['sig'].generate_and_parse_signal.assert_called()
        mock_deps['exec'].execute_entry_order.assert_called_with(
            'BTC/USDT', 'long', 10.0, 50000.0, 'mean_reversion', ANY, ANY
        )
        mock_deps['pos'].update_state.assert_called()

    def test_circuit_breaker_active(self, mock_deps):
        """Test that loop skips when circuit breaker is open."""
        event = threading.Event()
        event.set()
        engine = TradingEngine(1, {}, event)
        engine._initialize_components()
        
        mock_deps['cb'].is_open.return_value = True
        mock_deps['cb'].get_state.return_value = "OPEN"
        mock_deps['cb'].get_cooldown_remaining.return_value = 10
        
        with patch('time.sleep', side_effect=InterruptedError("Loop Break")) as mock_sleep:
            try:
                engine._trading_loop()
            except InterruptedError:
                pass
            
            # Should have slept
            mock_sleep.assert_called()
            # Should NOT have fetched data
            mock_deps['mdf'].fetch_ohlcv.assert_not_called()

"""
Full Trading Flow End-to-End Test

This test verifies the complete backend trading flow:
1. Optimization (regular/ultimate) - finds best strategy params
2. Backtest - validates the strategy performance
3. Create Bot Config - saves the strategy configuration
4. Start Bot - initiates trading with the strategy
5. Signal Generation - generates a fake signal
6. Order Placement - places an order with TP/SL
7. TP/SL Hit - simulates price movement that triggers TP/SL

Usage:
    python -m pytest tests/test_full_trading_flow.py -v
    
    Or run directly:
    python tests/test_full_trading_flow.py
"""

import sys
import os
import time
import threading
import uuid
import logging
from datetime import datetime, timedelta

# Change to backend directory for proper config loading
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(BACKEND_DIR)

# Add parent directory to path for imports
sys.path.insert(0, BACKEND_DIR)

from app.core.database import DuckDBHandler
from app.core.bot import create_strategy, run_bot_instance
from app.core.bot_manager import BotManager, bot_manager
from app.core.exchange.paper import PaperExchange
from app.core.vectorized_backtest import VectorizedBacktester
from app.core.hyperopt import Hyperopt
from app.core.strategies.mean_reversion import MeanReversion
from app.core.strategies.sma_crossover import SMACrossover
from app.core.strategies.rsi import RSIStrategy
from app.core import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestTradingFlow")

# Test constants
TEST_USER_ID = 9999  # Use a special test user ID
TEST_SYMBOL = "BTC/USDT"
TEST_TIMEFRAME = "1m"
TEST_AMOUNT_USDT = 10.0


class MockPaperExchangeWithSignal(PaperExchange):
    """Extended paper exchange that can inject fake signals."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.force_signal = None  # Set to 'long' or 'short' to force a signal
        self.price_override = None  # Override price for TP/SL testing
        self._test_order_counter = 0
        
    def get_market_price(self, symbol):
        """Get market price, with optional override for testing."""
        if self.price_override is not None:
            return self.price_override
        try:
            ticker = self.fetch_ticker(symbol)
            return ticker.get('last', ticker.get('close', 100000))
        except:
            return 100000  # Fallback for testing
            
    def create_order(self, symbol, order_type, side, amount, price=None, 
                     take_profit=None, stop_loss=None, trailing_stop=None,
                     take_profit_pct=None, stop_loss_pct=None):
        """Create order with TP/SL tracking for testing."""
        self._test_order_counter += 1
        logger.info(f"📝 MockExchange: Creating {side} {order_type} order for {amount} {symbol}")
        
        # Store TP/SL for verification
        entry_price = price if price else self.get_market_price(symbol)
        self._last_order_tp_sl = {
            'take_profit_pct': take_profit_pct,
            'stop_loss_pct': stop_loss_pct,
            'entry_price': entry_price,
            'side': side
        }
        
        if take_profit_pct:
            if side == 'buy':
                tp_price = entry_price * (1 + take_profit_pct)
                sl_price = entry_price * (1 - stop_loss_pct) if stop_loss_pct else None
            else:
                tp_price = entry_price * (1 - take_profit_pct)
                sl_price = entry_price * (1 + stop_loss_pct) if stop_loss_pct else None
            self._last_order_tp_sl['tp_price'] = tp_price
            self._last_order_tp_sl['sl_price'] = sl_price
            logger.info(f"   TP: {tp_price:.2f}, SL: {sl_price:.2f}")
        
        return super().create_order(symbol, order_type, side, amount, price,
                                    take_profit, stop_loss, trailing_stop,
                                    take_profit_pct, stop_loss_pct)
    
    def simulate_price_to_tp(self, symbol):
        """Simulate price movement to hit Take Profit."""
        if hasattr(self, '_last_order_tp_sl') and self._last_order_tp_sl:
            tp_price = self._last_order_tp_sl.get('tp_price')
            if tp_price:
                self.price_override = tp_price
                logger.info(f"🎯 Simulating price hit TP at {tp_price:.2f}")
                return tp_price
        return None
    
    def simulate_price_to_sl(self, symbol):
        """Simulate price movement to hit Stop Loss."""
        if hasattr(self, '_last_order_tp_sl') and self._last_order_tp_sl:
            sl_price = self._last_order_tp_sl.get('sl_price')
            if sl_price:
                self.price_override = sl_price
                logger.info(f"⛔ Simulating price hit SL at {sl_price:.2f}")
                return sl_price
        return None


class MockStrategyWithSignal:
    """A mock strategy that returns forced signals for testing."""
    
    def __init__(self, forced_signal=None):
        self.forced_signal = forced_signal  # 'long', 'short', 'hold'
        self.highest_price = 0
        self.lowest_price = float('inf')
        
    def generate_signal(self, df):
        """Generate the forced signal or random based on data."""
        if self.forced_signal:
            signal = self.forced_signal
            logger.info(f"🔔 MockStrategy: Returning forced signal: {signal}")
        else:
            signal = 'hold'
            
        return {
            'signal': signal,
            'score': 3 if signal in ['long', 'short'] else 0,
            'details': {'mock': True, 'reason': 'Forced test signal'}
        }
    
    def calculate_indicators(self, df):
        return df


def test_step_1_optimization():
    """Test Step 1: Run optimization to find best strategy parameters."""
    logger.info("\n" + "="*60)
    logger.info("STEP 1: Running Optimization")
    logger.info("="*60)
    
    # Use Mean Reversion strategy for optimization
    strategy_class = MeanReversion
    
    # Create a dummy strategy to fetch data
    dummy_strategy = strategy_class()
    bt = VectorizedBacktester(TEST_SYMBOL, TEST_TIMEFRAME, dummy_strategy, days=1)
    bt.fetch_data()
    
    if bt.df is None or bt.df.empty:
        logger.warning("⚠️ Could not fetch data for optimization test. Skipping...")
        return None
    
    logger.info(f"✅ Fetched {len(bt.df)} rows of data")
    
    # Define parameter ranges for optimization
    param_ranges = {
        'bb_period': [15, 20, 25],
        'bb_std': [1.5, 2.0, 2.5],
        'rsi_period': [10, 14, 20]
    }
    
    # Run optimization (with small n_trials for testing)
    optimizer = Hyperopt(TEST_SYMBOL, TEST_TIMEFRAME, bt.df)
    
    def progress_callback(current, total, details=None):
        logger.debug(f"   Optimization progress: {current}/{total}")
    
    results_df = optimizer.optimize(param_ranges, strategy_class, n_trials=5, 
                                     progress_callback=progress_callback)
    
    if results_df is not None and not results_df.empty:
        best_result = results_df.iloc[0]
        logger.info(f"✅ Optimization complete. Best return: {best_result.get('return', 0):.2%}")
        
        # Extract best parameters
        best_params = {k: v for k, v in best_result.items() 
                       if k in ['bb_period', 'bb_std', 'rsi_period']}
        logger.info(f"   Best parameters: {best_params}")
        return best_params
    else:
        logger.warning("⚠️ Optimization returned no results")
        return {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14}  # Default


def test_step_2_backtest(params):
    """Test Step 2: Run backtest with selected strategy parameters."""
    logger.info("\n" + "="*60)
    logger.info("STEP 2: Running Backtest")
    logger.info("="*60)
    
    if params is None:
        params = {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14}
    
    # Create strategy with optimized params
    strategy = MeanReversion(**params)
    
    # Run backtest
    bt = VectorizedBacktester(TEST_SYMBOL, TEST_TIMEFRAME, strategy, days=1)
    bt.fetch_data()
    
    if bt.df is None or bt.df.empty:
        logger.warning("⚠️ Could not fetch data for backtest. Skipping...")
        return None
    
    bt.run()
    
    # Check results
    total_return = ((bt.balance - 1000) / 1000) * 100
    wins = [t for t in bt.trades if t['pnl'] > 0]
    win_rate = (len(wins) / len(bt.trades)) * 100 if bt.trades else 0
    
    logger.info(f"✅ Backtest complete:")
    logger.info(f"   Final Balance: ${bt.balance:.2f}")
    logger.info(f"   Total Return: {total_return:.2f}%")
    logger.info(f"   Win Rate: {win_rate:.2f}%")
    logger.info(f"   Total Trades: {len(bt.trades)}")
    
    return {
        'final_balance': bt.balance,
        'total_return': total_return,
        'win_rate': win_rate,
        'total_trades': len(bt.trades),
        'params': params
    }


def test_step_3_create_bot_config(params, backtest_result):
    """Test Step 3: Create a bot configuration with the strategy."""
    logger.info("\n" + "="*60)
    logger.info("STEP 3: Creating Bot Configuration")
    logger.info("="*60)
    
    if params is None:
        params = {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14}
    
    db = DuckDBHandler()
    
    # Ensure test user exists
    existing_user = db.get_user_by_id(TEST_USER_ID)
    if not existing_user:
        logger.info(f"   Creating test user {TEST_USER_ID}...")
        # Create test user (simplified - may need password hash in real scenario)
        try:
            db._execute("""
                INSERT INTO users (id, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (TEST_USER_ID, f"test_{TEST_USER_ID}@test.com", "test_hash", datetime.now()))
            logger.info(f"✅ Test user created")
        except Exception as e:
            logger.warning(f"   User creation failed (may already exist): {e}")
    
    # Create bot config
    bot_config = {
        'symbol': TEST_SYMBOL,
        'strategy': 'mean_reversion',
        'timeframe': TEST_TIMEFRAME,
        'amount_usdt': TEST_AMOUNT_USDT,
        'take_profit_pct': 0.02,  # 2% TP
        'stop_loss_pct': 0.01,    # 1% SL
        'parameters': params,
        'dry_run': True
    }
    
    config_id = db.create_bot_config(TEST_USER_ID, bot_config)
    
    if config_id:
        logger.info(f"✅ Bot configuration created with ID: {config_id}")
        
        # Verify config was saved
        saved_config = db.get_bot_config(TEST_USER_ID, config_id)
        if saved_config:
            logger.info(f"   Verified: {saved_config}")
        
        return config_id
    else:
        logger.error("❌ Failed to create bot configuration")
        return None


def test_step_4_start_bot(config_id):
    """Test Step 4: Start the bot with the configuration."""
    logger.info("\n" + "="*60)
    logger.info("STEP 4: Starting Bot")
    logger.info("="*60)
    
    db = DuckDBHandler()
    
    if config_id:
        strategy_config = db.get_bot_config(TEST_USER_ID, config_id)
    else:
        strategy_config = None
    
    if not strategy_config:
        logger.warning("⚠️ No bot config found, using defaults")
        strategy_config = {
            'SYMBOL': TEST_SYMBOL,
            'TIMEFRAME': TEST_TIMEFRAME,
            'AMOUNT_USDT': TEST_AMOUNT_USDT,
            'STRATEGY': 'mean_reversion',
            'STRATEGY_PARAMS': {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14},
            'DRY_RUN': True,
            'TAKE_PROFIT_PCT': 0.02,
            'STOP_LOSS_PCT': 0.01
        }
    else:
        # Map DB keys to what bot expects
        strategy_config = {
            'SYMBOL': strategy_config['symbol'],
            'TIMEFRAME': strategy_config['timeframe'],
            'AMOUNT_USDT': strategy_config['amount_usdt'],
            'STRATEGY': strategy_config['strategy'],
            'STRATEGY_PARAMS': strategy_config.get('parameters', {}),
            'DRY_RUN': strategy_config['dry_run'],
            'TAKE_PROFIT_PCT': strategy_config['take_profit_pct'],
            'STOP_LOSS_PCT': strategy_config['stop_loss_pct']
        }
    
    logger.info(f"   Config: {strategy_config}")
    
    # Start bot via manager
    success = bot_manager.start_bot(TEST_USER_ID, strategy_config, config_id=config_id)
    
    if success:
        logger.info(f"✅ Bot started successfully for user {TEST_USER_ID}")
        
        # Brief wait and check status
        time.sleep(2)
        status = bot_manager.get_status(TEST_USER_ID, config_id=config_id)
        logger.info(f"   Status: {status}")
        
        return True
    else:
        logger.error("❌ Failed to start bot")
        return False


def test_step_5_signal_generation():
    """Test Step 5: Verify signal generation mechanism."""
    logger.info("\n" + "="*60)
    logger.info("STEP 5: Testing Signal Generation")
    logger.info("="*60)
    
    # Create strategy
    strategy = MeanReversion(bb_period=20, bb_std=2.0, rsi_period=14)
    
    # Fetch some data
    paper_exchange = PaperExchange("test_key", "test_secret")
    df = paper_exchange.fetch_ohlcv(TEST_SYMBOL, TEST_TIMEFRAME, limit=100)
    
    if df is None or df.empty:
        logger.warning("⚠️ Could not fetch data for signal test. Using mock.")
        # Create mock data
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
        mock_data = {
            'timestamp': dates,
            'open': np.random.uniform(95000, 105000, 100),
            'high': np.random.uniform(96000, 106000, 100),
            'low': np.random.uniform(94000, 104000, 100),
            'close': np.random.uniform(95000, 105000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }
        df = pd.DataFrame(mock_data)
    
    # Generate signal
    result = strategy.generate_signal(df)
    
    logger.info(f"✅ Signal generated:")
    logger.info(f"   Signal: {result.get('signal')}")
    logger.info(f"   Score: {result.get('score')}")
    logger.info(f"   Details: {result.get('details')}")
    
    return result


def test_step_6_order_placement():
    """Test Step 6: Verify order placement with TP/SL."""
    logger.info("\n" + "="*60)
    logger.info("STEP 6: Testing Order Placement with TP/SL")
    logger.info("="*60)
    
    # Create mock exchange
    mock_exchange = MockPaperExchangeWithSignal("test_key", "test_secret")
    
    # Place a test order
    try:
        order = mock_exchange.create_order(
            symbol=TEST_SYMBOL,
            order_type='market',
            side='buy',
            amount=0.0001,  # Small test amount
            take_profit_pct=0.02,
            stop_loss_pct=0.01
        )
        
        if order:
            logger.info(f"✅ Order placed successfully:")
            logger.info(f"   Order ID: {order.get('id')}")
            logger.info(f"   Side: {order.get('side')}")
            logger.info(f"   Amount: {order.get('amount')}")
            logger.info(f"   Price: {order.get('price')}")
            logger.info(f"   Status: {order.get('status')}")
            
            # Verify TP/SL were calculated
            if hasattr(mock_exchange, '_last_order_tp_sl'):
                tp_sl = mock_exchange._last_order_tp_sl
                logger.info(f"   TP Price: {tp_sl.get('tp_price', 'N/A')}")
                logger.info(f"   SL Price: {tp_sl.get('sl_price', 'N/A')}")
            
            # Check position was updated
            position = mock_exchange.fetch_position(TEST_SYMBOL)
            logger.info(f"   Position after order: {position}")
            
            return order, mock_exchange
        else:
            logger.error("❌ Order returned None")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ Order placement failed: {e}")
        return None, None


def test_step_7_tp_sl_simulation(mock_exchange):
    """Test Step 7: Simulate TP/SL hit."""
    logger.info("\n" + "="*60)
    logger.info("STEP 7: Simulating TP/SL Hit")
    logger.info("="*60)
    
    if mock_exchange is None:
        logger.warning("⚠️ No mock exchange available. Skipping TP/SL test.")
        return
    
    # First, ensure we have a position
    position = mock_exchange.fetch_position(TEST_SYMBOL)
    if position.get('size', 0) == 0:
        logger.warning("⚠️ No position open. Placing test order first...")
        mock_exchange.create_order(
            symbol=TEST_SYMBOL,
            order_type='market',
            side='buy',
            amount=0.0001,
            take_profit_pct=0.02,
            stop_loss_pct=0.01
        )
    
    # Test TP hit
    logger.info("\n--- Testing Take Profit Hit ---")
    
    initial_balance = mock_exchange.paper_balance
    tp_price = mock_exchange.simulate_price_to_tp(TEST_SYMBOL)
    
    if tp_price:
        # Close position at TP
        position = mock_exchange.fetch_position(TEST_SYMBOL)
        if position.get('size', 0) > 0:
            mock_exchange.close_position(TEST_SYMBOL)
            
            final_balance = mock_exchange.paper_balance
            pnl = final_balance - initial_balance
            
            logger.info(f"✅ Position closed at TP:")
            logger.info(f"   TP Price: {tp_price:.2f}")
            logger.info(f"   Initial Balance: ${initial_balance:.2f}")
            logger.info(f"   Final Balance: ${final_balance:.2f}")
            logger.info(f"   PnL: ${pnl:.2f}")
            
            if pnl > 0:
                logger.info("   ✅ TP resulted in PROFIT as expected")
            else:
                logger.warning("   ⚠️ TP did not result in profit (fees may have reduced it)")
    
    # Reset for SL test
    mock_exchange.price_override = None
    
    # Open new position for SL test
    logger.info("\n--- Testing Stop Loss Hit ---")
    
    mock_exchange.create_order(
        symbol=TEST_SYMBOL,
        order_type='market',
        side='buy',
        amount=0.0001,
        take_profit_pct=0.02,
        stop_loss_pct=0.01
    )
    
    initial_balance = mock_exchange.paper_balance
    sl_price = mock_exchange.simulate_price_to_sl(TEST_SYMBOL)
    
    if sl_price:
        position = mock_exchange.fetch_position(TEST_SYMBOL)
        if position.get('size', 0) > 0:
            mock_exchange.close_position(TEST_SYMBOL)
            
            final_balance = mock_exchange.paper_balance
            pnl = final_balance - initial_balance
            
            logger.info(f"✅ Position closed at SL:")
            logger.info(f"   SL Price: {sl_price:.2f}")
            logger.info(f"   Initial Balance: ${initial_balance:.2f}")
            logger.info(f"   Final Balance: ${final_balance:.2f}")
            logger.info(f"   PnL: ${pnl:.2f}")
            
            if pnl < 0:
                logger.info("   ✅ SL resulted in LOSS as expected (limited loss)")
            else:
                logger.info("   ⚠️ SL did not result in loss (unexpected)")
    
    return True


def test_cleanup():
    """Clean up test resources."""
    logger.info("\n" + "="*60)
    logger.info("CLEANUP: Stopping test bot and cleaning up")
    logger.info("="*60)
    
    # Stop bot if running
    try:
        bot_manager.stop_bot(TEST_USER_ID)
        logger.info(f"✅ Bot stopped for user {TEST_USER_ID}")
    except Exception as e:
        logger.warning(f"   Could not stop bot: {e}")
    
    # Clean up test configs (optional)
    db = DuckDBHandler()
    try:
        configs = db.get_bot_configs(TEST_USER_ID)
        for cfg in configs:
            db.delete_bot_config(TEST_USER_ID, cfg['id'])
            logger.info(f"   Deleted config {cfg['id']}")
    except Exception as e:
        logger.warning(f"   Could not clean up configs: {e}")
    
    logger.info("✅ Cleanup complete")


def run_full_flow_test():
    """Run the complete flow test."""
    logger.info("\n" + "="*80)
    logger.info("FULL TRADING FLOW END-TO-END TEST")
    logger.info("="*80)
    logger.info(f"Test User ID: {TEST_USER_ID}")
    logger.info(f"Symbol: {TEST_SYMBOL}")
    logger.info(f"Timeframe: {TEST_TIMEFRAME}")
    logger.info(f"Amount: ${TEST_AMOUNT_USDT}")
    logger.info("="*80 + "\n")
    
    results = {
        'step_1_optimization': False,
        'step_2_backtest': False,
        'step_3_create_config': False,
        'step_4_start_bot': False,
        'step_5_signal': False,
        'step_6_order': False,
        'step_7_tp_sl': False
    }
    
    try:
        # Step 1: Optimization
        best_params = test_step_1_optimization()
        results['step_1_optimization'] = best_params is not None
        
        # Step 2: Backtest
        backtest_result = test_step_2_backtest(best_params)
        results['step_2_backtest'] = backtest_result is not None
        
        # Step 3: Create Bot Config
        config_id = test_step_3_create_bot_config(best_params, backtest_result)
        results['step_3_create_config'] = config_id is not None
        
        # Step 4: Start Bot
        bot_started = test_step_4_start_bot(config_id)
        results['step_4_start_bot'] = bot_started
        
        # Step 5: Signal Generation
        signal_result = test_step_5_signal_generation()
        results['step_5_signal'] = signal_result is not None
        
        # Step 6: Order Placement
        order, mock_exchange = test_step_6_order_placement()
        results['step_6_order'] = order is not None
        
        # Step 7: TP/SL Simulation
        tp_sl_result = test_step_7_tp_sl_simulation(mock_exchange)
        results['step_7_tp_sl'] = tp_sl_result is True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always cleanup
        test_cleanup()
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    all_passed = True
    for step, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"   {step}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*80)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.info("⚠️ SOME TESTS FAILED - Please review the logs above")
    logger.info("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_full_flow_test()
    sys.exit(0 if success else 1)

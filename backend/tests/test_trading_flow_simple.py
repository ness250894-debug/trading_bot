"""
Simplified Trading Flow Test - Tests the core flow step by step.
"""
import sys
import os

# Setup paths first
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
os.chdir(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

# Load .env file BEFORE importing app modules
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestFlow")

def run_test():
    results = {}
    
    # Step 1: Test Strategy Creation
    print("\n" + "="*60)
    print("STEP 1: Testing Strategy Creation")
    print("="*60)
    try:
        from app.core.bot import create_strategy
        strategy = create_strategy('mean_reversion', {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14})
        print(f"✅ Strategy created: {type(strategy).__name__}")
        results['strategy_creation'] = True
    except Exception as e:
        print(f"❌ Strategy creation failed: {e}")
        results['strategy_creation'] = False
    
    # Step 2: Test Paper Exchange
    print("\n" + "="*60)
    print("STEP 2: Testing Paper Exchange")
    print("="*60)
    try:
        from app.core.exchange.paper import PaperExchange
        # Use API keys from environment
        api_key = os.getenv('BYBIT_API_KEY', 'test_key')
        api_secret = os.getenv('BYBIT_API_SECRET', 'test_secret')
        paper = PaperExchange(api_key, api_secret, initial_balance=1000.0)
        balance = paper.fetch_balance()
        print(f"✅ Paper exchange created with balance: ${balance['USDT']['total']:.2f}")
        results['paper_exchange'] = True
    except Exception as e:
        print(f"❌ Paper exchange failed: {e}")
        results['paper_exchange'] = False
    
    # Step 3: Test Data Fetching
    print("\n" + "="*60)
    print("STEP 3: Testing Data Fetching")
    print("="*60)
    try:
        df = paper.fetch_ohlcv("BTC/USDT", "1m", limit=50)
        if df is not None and not df.empty:
            print(f"✅ Fetched {len(df)} candles for BTC/USDT")
            results['data_fetching'] = True
        else:
            print("⚠️ Data is empty")
            results['data_fetching'] = False
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        results['data_fetching'] = False
    
    # Step 4: Test Signal Generation
    print("\n" + "="*60)
    print("STEP 4: Testing Signal Generation")
    print("="*60)
    try:
        if results.get('data_fetching'):
            signal_result = strategy.generate_signal(df)
            print(f"✅ Signal generated: {signal_result.get('signal')}")
            print(f"   Score: {signal_result.get('score')}")
            print(f"   Details: {signal_result.get('details')}")
            results['signal_generation'] = True
        else:
            print("⚠️ Skipping - no data")
            results['signal_generation'] = False
    except Exception as e:
        print(f"❌ Signal generation failed: {e}")
        results['signal_generation'] = False
    
    # Step 5: Test Order Placement
    print("\n" + "="*60)
    print("STEP 5: Testing Order Placement with TP/SL")
    print("="*60)
    try:
        if results.get('paper_exchange'):
            order = paper.create_order(
                symbol="BTC/USDT",
                order_type="market",
                side="buy",
                amount=0.0001,
                take_profit_pct=0.02,
                stop_loss_pct=0.01
            )
            if order:
                print(f"✅ Order placed: {order.get('id')}")
                print(f"   Side: {order.get('side')}")
                print(f"   Amount: {order.get('amount')}")
                print(f"   Price: {order.get('price')}")
                results['order_placement'] = True
            else:
                print("❌ Order returned None")
                results['order_placement'] = False
        else:
            print("⚠️ Skipping - no exchange")
            results['order_placement'] = False
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        import traceback
        traceback.print_exc()
        results['order_placement'] = False
    
    # Step 6: Test Position Check
    print("\n" + "="*60)
    print("STEP 6: Testing Position Check")
    print("="*60)
    try:
        if results.get('order_placement'):
            position = paper.fetch_position("BTC/USDT")
            print(f"✅ Position fetched:")
            print(f"   Size: {position.get('size')}")
            print(f"   Side: {position.get('side')}")
            print(f"   Entry Price: {position.get('entry_price')}")
            results['position_check'] = position.get('size', 0) > 0
        else:
            print("⚠️ Skipping - no order")
            results['position_check'] = False
    except Exception as e:
        print(f"❌ Position check failed: {e}")
        results['position_check'] = False
    
    # Step 7: Test Position Close (TP simulation)
    print("\n" + "="*60)
    print("STEP 7: Testing Position Close (TP/SL simulation)")
    print("="*60)
    try:
        if results.get('position_check'):
            initial_balance = paper.paper_balance
            close_result = paper.close_position("BTC/USDT")
            final_balance = paper.paper_balance
            pnl = final_balance - initial_balance
            
            print(f"✅ Position closed:")
            print(f"   Initial Balance: ${initial_balance:.2f}")
            print(f"   Final Balance: ${final_balance:.2f}")
            print(f"   PnL: ${pnl:.4f}")
            results['position_close'] = True
        else:
            print("⚠️ Skipping - no position")
            results['position_close'] = False
    except Exception as e:
        print(f"❌ Position close failed: {e}")
        results['position_close'] = False
    
    # Step 8: Test Bot Manager
    print("\n" + "="*60)
    print("STEP 8: Testing Bot Manager")
    print("="*60)
    try:
        from app.core.bot_manager import bot_manager
        status = bot_manager.get_status(9999)  # Test user
        print(f"✅ Bot manager works. Status for test user: {status}")
        results['bot_manager'] = True
    except Exception as e:
        print(f"❌ Bot manager failed: {e}")
        results['bot_manager'] = False
    
    # Step 9: Test Database
    print("\n" + "="*60)
    print("STEP 9: Testing Database Operations")
    print("="*60)
    try:
        from app.core.database import DuckDBHandler
        db = DuckDBHandler()
        
        # Get first existing user for testing
        all_users = db.get_all_users()
        if all_users:
            test_user_id = all_users[0]['id']
            print(f"   Using existing user ID: {test_user_id}")
        else:
            test_user_id = 1
            print(f"   No users found, using ID: {test_user_id}")
        
        # Create test bot config
        test_config = {
            'symbol': 'BTC/USDT',
            'strategy': 'mean_reversion',
            'timeframe': '1m',
            'amount_usdt': 10.0,
            'take_profit_pct': 0.02,
            'stop_loss_pct': 0.01,
            'parameters': {'bb_period': 20},
            'dry_run': True
        }
        
        config_id = db.create_bot_config(test_user_id, test_config)
        if config_id:
            print(f"✅ Bot config created with ID: {config_id}")
            
            # Verify
            saved = db.get_bot_config(test_user_id, config_id)
            print(f"   Verified config: symbol={saved.get('symbol')}, strategy={saved.get('strategy')}")
            
            # Clean up
            db.delete_bot_config(test_user_id, config_id)
            print(f"   Cleaned up test config")
            results['database'] = True
        else:
            print("❌ Failed to create bot config (may need user first)")
            results['database'] = False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        results['database'] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for step, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {step}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Backend flow is working correctly.")
    else:
        print("⚠️ SOME TESTS FAILED - Check the details above.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)

import sys
import os
import threading
import time
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.bot_manager import BotManager, BotInstance
from app.core.bot import run_bot_instance
from app.core.database import DuckDBHandler

def test_active_trades_logic():
    print("Testing active_trades logic...")
    
    # Mock dependencies
    user_id = 123
    strategy_config = {"SYMBOL": "BTC/USDT", "STRATEGY": "mean_reversion"}
    
    # Create BotInstance
    instance = BotInstance(user_id, strategy_config)
    print(f"Initial active_trades: {instance.get_status()['active_trades']}")
    assert instance.get_status()['active_trades'] == 0
    
    # Simulate Bot Loop updating state
    print("Simulating bot loop updating state...")
    instance.runtime_state['active_trades'] = 1
    print(f"Updated active_trades: {instance.get_status()['active_trades']}")
    assert instance.get_status()['active_trades'] == 1
    
    instance.runtime_state['active_trades'] = 0
    print(f"Final active_trades: {instance.get_status()['active_trades']}")
    assert instance.get_status()['active_trades'] == 0
    print("✅ active_trades logic passed")

def test_database_retry():
    print("\nTesting database retry logic...")
    db = DuckDBHandler()
    
    # Mock the connection object
    db.conn = MagicMock()
    
    attempts = 0
    def side_effect(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            print(f"  Attempt {attempts}: Simulating DB failure")
            raise Exception("Simulated DB Error")
        print(f"  Attempt {attempts}: Success")
        return MagicMock()
    
    # Set the side effect on the mock's execute method
    db.conn.execute.side_effect = side_effect

    # Call a method with @retry
    print("Calling save_user_strategy with retry...")
    result = db.save_user_strategy(999, {"SYMBOL": "TEST"})
    
    if result:
        print("✅ Retry logic worked, operation succeeded")
    else:
        print("❌ Retry logic failed")
            
    # Verify attempts
    # Expected: 1 (fail) + 1 (fail) + 2 (success: select + update/insert) = 4
    print(f"Total attempts: {attempts}")
    assert attempts == 4

if __name__ == "__main__":
    try:
        test_active_trades_logic()
        test_database_retry()
        print("\n🎉 All verification tests passed!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

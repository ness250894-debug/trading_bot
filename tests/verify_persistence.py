import sys
import os
import logging
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import DuckDBHandler
from app.core.exchange.paper import PaperExchange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersistenceTest")

def test_persistence():
    logger.info("Testing State Persistence...")
    
    db = DuckDBHandler()
    user_id = 999 # Test User
    
    # 1. Setup Test User
    logger.info("Setting up test user...")
    try:
        db.conn.execute("DELETE FROM user_strategies WHERE user_id = ?", [user_id])
        # Note: 'id' is primary key, we need to provide it or rely on sequence if set. 
        # Assuming simple integer for now.
        db.conn.execute("""
            INSERT INTO user_strategies (id, user_id, symbol, timeframe, amount_usdt, strategy, dry_run, exchange)
            VALUES (99999, ?, 'BTC/USDT', '1m', 100.0, 'mean_reversion', true, 'bybit')
        """, [user_id])
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

    # 2. Test update_bot_state
    logger.info("Testing update_bot_state...")
    start_time = datetime.now()
    order_id = "test_order_123"
    
    success = db.update_bot_state(user_id, position_start_time=start_time, active_order_id=order_id)
    if not success:
        logger.error("update_bot_state failed")
        return False
        
    # Verify Read
    strategy = db.get_user_strategy(user_id)
    if not strategy:
        logger.error("Failed to read strategy")
        return False
        
    fetched_time = strategy.get('position_start_time')
    fetched_order = strategy.get('active_order_id')
    
    logger.info(f"Fetched Time: {fetched_time}")
    logger.info(f"Fetched Order: {fetched_order}")
    
    # Check values (allow small time diff due to DB storage precision)
    if str(fetched_order) != order_id:
        logger.error(f"Order ID mismatch. Expected {order_id}, got {fetched_order}")
        return False
        
    if not fetched_time:
        logger.error("Time not saved")
        return False
        
    logger.info("✅ Database Persistence Verified")
    
    # 3. Test Partial Update (Clear Order, Keep Time)
    logger.info("Testing Partial Update (Clear Order)...")
    db.update_bot_state(user_id, active_order_id=None, position_start_time='NO_CHANGE')
    
    strategy = db.get_user_strategy(user_id)
    if strategy.get('active_order_id') is not None:
        logger.error("Failed to clear active_order_id")
        return False
    if strategy.get('position_start_time') is None: # Should still be there
        logger.error("position_start_time was accidentally cleared")
        return False
        
    logger.info("✅ Partial Update Verified")
    
    # Cleanup
    db.conn.execute("DELETE FROM user_strategies WHERE user_id = ?", [user_id])
    return True

if __name__ == "__main__":
    if test_persistence():
        sys.exit(0)
    else:
        sys.exit(1)

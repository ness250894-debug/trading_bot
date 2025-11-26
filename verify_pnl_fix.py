import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import DuckDBHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyFix")

def verify_pnl():
    db = DuckDBHandler("test_pnl.duckdb")
    
    # Clear existing trades
    db.conn.execute("DROP TABLE IF EXISTS trades")
    db.conn.execute("DROP SEQUENCE IF EXISTS seq_trade_id")
    
    # Insert mock trades
    trades = [
        {'symbol': 'BTC/USDT', 'side': 'Buy', 'price': 50000, 'amount': 0.1, 'type': 'OPEN', 'pnl': None},
        {'symbol': 'BTC/USDT', 'side': 'Sell', 'price': 51000, 'amount': 0.1, 'type': 'CLOSE', 'pnl': 100.0}, # +100
        {'symbol': 'BTC/USDT', 'side': 'Sell', 'price': 51000, 'amount': 0.1, 'type': 'OPEN', 'pnl': None},
        {'symbol': 'BTC/USDT', 'side': 'Buy', 'price': 50500, 'amount': 0.1, 'type': 'CLOSE', 'pnl': 50.0}, # +50
        {'symbol': 'BTC/USDT', 'side': 'Buy', 'price': 50000, 'amount': 0.1, 'type': 'OPEN', 'pnl': None},
        {'symbol': 'BTC/USDT', 'side': 'Sell', 'price': 49000, 'amount': 0.1, 'type': 'CLOSE', 'pnl': -100.0}, # -100
    ]
    
    logger.info("Inserting mock trades...")
    for t in trades:
        db.save_trade(t)
        
    # Expected PnL: 100 + 50 - 100 = 50
    expected_pnl = 50.0
    
    logger.info("Calculating total PnL...")
    total_pnl = db.get_total_pnl()
    
    logger.info(f"Expected PnL: {expected_pnl}")
    logger.info(f"Actual PnL: {total_pnl}")
    
    if abs(total_pnl - expected_pnl) < 0.01:
        logger.info("✅ Verification SUCCESS: PnL calculation is correct.")
        
        # Verify get_trades limit doesn't affect it
        # Insert 60 more trades with 0 PnL
        logger.info("Inserting 60 dummy trades...")
        for i in range(60):
             db.save_trade({'symbol': 'BTC/USDT', 'side': 'Buy', 'price': 50000, 'amount': 0.1, 'type': 'CLOSE', 'pnl': 0.0})
             
        total_pnl_after = db.get_total_pnl()
        logger.info(f"Total PnL after dummy trades: {total_pnl_after}")
        
        if abs(total_pnl_after - expected_pnl) < 0.01:
             logger.info("✅ Verification SUCCESS: PnL calculation ignores limit.")
        else:
             logger.error("❌ Verification FAILED: PnL calculation affected by limit.")
             
    else:
        logger.error("❌ Verification FAILED: PnL calculation is incorrect.")

    # Cleanup
    import os
    try:
        os.remove("test_pnl.duckdb")
    except:
        pass

if __name__ == "__main__":
    verify_pnl()

import duckdb
import sys
import os

from app.core.database import DuckDBHandler
from app.core import config

def seed_data():
    # Use the handler to ensure we're using the same DB as the app
    db = DuckDBHandler(config.DB_PATH)
    conn = db.conn
    
    # Insert trades for User 1
    conn.execute("DELETE FROM trades WHERE symbol LIKE 'TEST%'")
    
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, type, pnl, strategy)
        VALUES (nextval('seq_trade_id'), 1, CURRENT_TIMESTAMP, 'TEST/USER1', 'Buy', 50000, 0.1, 'OPEN', 0, 'Test')
    """)
    
    # Insert trades for User 2
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, type, pnl, strategy)
        VALUES (nextval('seq_trade_id'), 2, CURRENT_TIMESTAMP, 'TEST/USER2', 'Buy', 60000, 0.1, 'OPEN', 0, 'Test')
    """)
    
    # Insert trades with NULL user_id (Legacy)
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, type, pnl, strategy)
        VALUES (nextval('seq_trade_id'), NULL, CURRENT_TIMESTAMP, 'TEST/LEGACY', 'Buy', 40000, 0.1, 'OPEN', 0, 'Test')
    """)
    
    # DuckDBHandler keeps connection open, so no need to explicitly close it here
    # as the script ends. The Handler doesn't expose close() directly on itself typically.
    print("Test data inserted.")

if __name__ == "__main__":
    seed_data()

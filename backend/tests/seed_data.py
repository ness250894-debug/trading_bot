import duckdb
import sys
import os

DB_FILE = "data/trading_bot.duckdb"

def seed_data():
    conn = duckdb.connect(DB_FILE)
    
    # Insert trades for User 1
    conn.execute("DELETE FROM trades WHERE symbol LIKE 'TEST%'")
    
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, total_value, type, pnl, strategy, leverage)
        VALUES (nextval('seq_trade_id'), 1, CURRENT_TIMESTAMP, 'TEST/USER1', 'Buy', 50000, 0.1, 5000, 'OPEN', 0, 'Test', 1.0)
    """)
    
    # Insert trades for User 2
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, total_value, type, pnl, strategy, leverage)
        VALUES (nextval('seq_trade_id'), 2, CURRENT_TIMESTAMP, 'TEST/USER2', 'Buy', 60000, 0.1, 6000, 'OPEN', 0, 'Test', 1.0)
    """)
    
    # Insert trades with NULL user_id (Legacy)
    conn.execute("""
        INSERT INTO trades (id, user_id, timestamp, symbol, side, price, amount, total_value, type, pnl, strategy, leverage)
        VALUES (nextval('seq_trade_id'), NULL, CURRENT_TIMESTAMP, 'TEST/LEGACY', 'Buy', 40000, 0.1, 4000, 'OPEN', 0, 'Test', 1.0)
    """)
    
    conn.close()
    print("Test data inserted.")

if __name__ == "__main__":
    seed_data()

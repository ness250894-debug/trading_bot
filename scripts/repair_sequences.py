import duckdb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DB_Repair")

DB_PATH = 'data/trading_bot.duckdb'

# Mapping of Sequence Name -> Table Name
# Based on grep results from repositories
SEQUENCES = {
    'seq_watchlist_id': 'watchlists',
    'seq_alert_id': 'price_alerts',
    'seq_pref_id': 'dashboard_preferences',
    'seq_user_strategy_id': 'user_strategies',
    'seq_bot_config_id': 'bot_configs',
    'seq_backtest_id': 'backtest_results',
    'seq_subscription_id': 'subscriptions',
    'seq_payment_id': 'payments',
    'seq_supported_symbol_id': 'supported_symbols',
    'seq_trade_id': 'trades',
    'seq_trade_note_id': 'trade_notes'
}

def repair_sequences():
    try:
        conn = duckdb.connect(DB_PATH)
        logger.info(f"Connected to {DB_PATH}")
        
        for seq_name, table_name in SEQUENCES.items():
            try:
                # 1. Get Max ID
                logger.info(f"Checking {table_name} for max ID...")
                # Check if table exists first
                table_check = conn.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'").fetchone()
                
                if not table_check:
                    logger.warning(f"Table {table_name} does not exist! Skipping {seq_name}.")
                    continue
                    
                result = conn.execute(f"SELECT MAX(id) FROM {table_name}").fetchone()
                max_id = result[0] if result and result[0] is not None else 0
                next_val = max_id + 1
                
                logger.info(f"Table {table_name}: Max ID = {max_id}. Next sequence value should be {next_val}.")
                
                # 2. Create Sequence
                # Drop if exists to be safe/reset? Or just create if not exists?
                # DuckDB: CREATE SEQUENCE [IF NOT EXISTS] name [START n]
                
                # Let's drop and recreate to ensure it starts at the right place
                conn.execute(f"DROP SEQUENCE IF EXISTS {seq_name}")
                conn.execute(f"CREATE SEQUENCE {seq_name} START {next_val}")
                
                logger.info(f"Successfully repaired {seq_name} (Start: {next_val})")
                
            except Exception as e:
                logger.error(f"Failed to repair {seq_name} for table {table_name}: {e}")
                
        logger.info("Sequence repair complete.")
        
    except Exception as e:
        logger.error(f"Critical error connecting to DB: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    repair_sequences()

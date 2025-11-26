import duckdb
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Database")

class DuckDBHandler:
    def __init__(self, db_file="trading_bot.duckdb"):
        self.db_file = db_file
        # Use read-write mode explicitly to avoid conflicts
        self.conn = duckdb.connect(db_file, read_only=False)
        self.create_tables()

    def create_tables(self):
        """Creates necessary tables if they don't exist."""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP,
                    strategy VARCHAR,
                    parameters VARCHAR,
                    return_pct DOUBLE,
                    win_rate_pct DOUBLE,
                    trades INTEGER,
                    final_balance DOUBLE
                );
                CREATE SEQUENCE IF NOT EXISTS seq_backtest_id START 1;
            """)
            logger.info("Tables checked/created.")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    def save_result(self, result):
        """
        Saves a backtest result to the database.
        result: dict containing strategy, params, return, win_rate, trades, final_balance
        """
        try:
            timestamp = datetime.now()
            query = """
                INSERT INTO backtest_results 
                (id, timestamp, strategy, parameters, return_pct, win_rate_pct, trades, final_balance)
                VALUES (nextval('seq_backtest_id'), ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                timestamp,
                result['strategy'],
                str(result['params']),
                result['return'],
                result['win_rate'],
                result['trades'],
                result['final_balance']
            ])
            logger.info("Result saved to DB.")
        except Exception as e:
            logger.error(f"Error saving result: {e}")

    def get_leaderboard(self):
        """Returns the leaderboard sorted by return."""
        try:
            df = self.conn.execute("SELECT * FROM backtest_results ORDER BY return_pct DESC").fetchdf()
            return df
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {e}")
            return pd.DataFrame()

    def clear_leaderboard(self):
        """Clears all backtest results."""
        try:
            self.conn.execute("DELETE FROM backtest_results")
            logger.info("Leaderboard cleared.")
        except Exception as e:
            logger.error(f"Error clearing leaderboard: {e}")

    def save_trade(self, trade_data):
        """
        Saves a trade to the database.
        trade_data: dict containing symbol, side, price, amount, type, pnl, strategy
        """
        try:
            timestamp = datetime.now()
            # Create table if not exists (lazy init for existing DBs)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP,
                    symbol VARCHAR,
                    side VARCHAR,
                    price DOUBLE,
                    amount DOUBLE,
                    type VARCHAR,
                    pnl DOUBLE,
                    strategy VARCHAR
                );
                CREATE SEQUENCE IF NOT EXISTS seq_trade_id START 1;
            """)
            
            query = """
                INSERT INTO trades 
                (id, timestamp, symbol, side, price, amount, type, pnl, strategy)
                VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                timestamp,
                trade_data['symbol'],
                trade_data['side'],
                trade_data['price'],
                trade_data['amount'],
                trade_data['type'], # 'OPEN' or 'CLOSE'
                trade_data.get('pnl'), # None for OPEN
                trade_data.get('strategy', 'Unknown')
            ])
            logger.info(f"Trade saved: {trade_data['side']} {trade_data['symbol']} ({trade_data['type']})")
        except Exception as e:
            logger.error(f"Error saving trade: {e}")

    def get_trades(self, limit=50):
        """Returns recent trades."""
        try:
            # Check if table exists first
            tables = self.conn.execute("SHOW TABLES").fetchall()
            if ('trades',) not in tables:
                return pd.DataFrame()

            df = self.conn.execute(f"SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}").fetchdf()
            # Convert timestamp to string for JSON serialization
            if not df.empty:
                df['timestamp'] = df['timestamp'].astype(str)
            return df
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return pd.DataFrame()

    def get_recent_trades(self, limit=10):
        """Returns recent trades as a list of dictionaries for internal logic."""
        try:
            df = self.get_trades(limit)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []

    def get_total_pnl(self):
        """Returns the sum of PnL for all trades."""
        try:
            # Check if table exists first
            tables = self.conn.execute("SHOW TABLES").fetchall()
            if ('trades',) not in tables:
                return 0.0
            
            # Sum pnl where it is not null
            result = self.conn.execute("SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL").fetchone()
            return result[0] if result and result[0] is not None else 0.0
        except Exception as e:
            logger.error(f"Error calculating total PnL: {e}")
            return 0.0

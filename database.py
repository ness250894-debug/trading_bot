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
        self.conn = duckdb.connect(db_file)
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
        """Clears all results."""
        try:
            self.conn.execute("DELETE FROM backtest_results")
            logger.info("Leaderboard cleared.")
        except Exception as e:
            logger.error(f"Error clearing leaderboard: {e}")

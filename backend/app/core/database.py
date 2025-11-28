import duckdb
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Database")

import os

class DuckDBHandler:
    def __init__(self, db_file="data/trading_bot.duckdb"):
        self.db_file = db_file
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
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
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR UNIQUE,
                    hashed_password VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_user_id START 1;
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
                    total_value DOUBLE,
                    type VARCHAR,
                    pnl DOUBLE,
                    strategy VARCHAR,
                    leverage DOUBLE
                );
                CREATE SEQUENCE IF NOT EXISTS seq_trade_id START 1;
            """)
            
            # Lazy Migration: Check if columns exist
            try:
                self.conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS total_value DOUBLE")
            except:
                pass
            try:
                self.conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS leverage DOUBLE")
            except:
                pass
            
            query = """
                INSERT INTO trades 
                (id, timestamp, symbol, side, price, amount, total_value, type, pnl, strategy, leverage)
                VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Calculate total_value if not provided
            total_value = trade_data.get('total_value', trade_data['price'] * trade_data['amount'])
            
            self.conn.execute(query, [
                timestamp,
                trade_data['symbol'],
                trade_data['side'],
                trade_data['price'],
                trade_data['amount'],
                total_value,
                trade_data['type'], # 'OPEN' or 'CLOSE'
                trade_data.get('pnl'), # None for OPEN
                trade_data.get('strategy', 'Unknown'),
                trade_data.get('leverage', 1.0)
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

    def clear_trades(self):
        """Deletes all trades from the database."""
        try:
            self.conn.execute("DELETE FROM trades")
            logger.info("All trades cleared from database.")
            return True
        except Exception as e:
            logger.error(f"Error clearing trades: {e}")
            return False

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

    def get_user_by_email(self, email):
        """Returns a user by email."""
        try:
            result = self.conn.execute("SELECT * FROM users WHERE email = ?", [email]).fetchone()
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "hashed_password": result[2],
                    "created_at": result[3]
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    def create_user(self, email, hashed_password):
        """Creates a new user."""
        try:
            timestamp = datetime.now()
            query = """
                INSERT INTO users (id, email, hashed_password, created_at)
                VALUES (nextval('seq_user_id'), ?, ?, ?)
            """
            self.conn.execute(query, [email, hashed_password, timestamp])
            logger.info(f"User created: {email}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False

    def get_user_strategy(self, user_id):
        """Get user's strategy configuration (stub for now)."""
        # TODO: Implement per-user strategy storage
        return None

    def save_user_strategy(self, user_id, strategy_config):
        """Save user's strategy configuration (stub for now)."""
        # TODO: Implement per-user strategy storage
        logger.info(f"Skipping strategy save for user {user_id} (not yet implemented)")
        return True

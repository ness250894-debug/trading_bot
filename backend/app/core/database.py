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
                    final_balance DOUBLE,
                    user_id INTEGER
                );
                CREATE SEQUENCE IF NOT EXISTS seq_backtest_id START 1;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR UNIQUE,
                    hashed_password VARCHAR,
                    telegram_bot_token VARCHAR,
                    telegram_chat_id VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_user_id START 1;
                CREATE TABLE IF NOT EXISTS user_strategies (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR,
                    timeframe VARCHAR,
                    amount_usdt DOUBLE,
                    strategy VARCHAR,
                    strategy_params VARCHAR,
                    dry_run BOOLEAN,
                    take_profit_pct DOUBLE,
                    stop_loss_pct DOUBLE,
                    updated_at TIMESTAMP,
                    UNIQUE(user_id)
                );
                CREATE SEQUENCE IF NOT EXISTS seq_user_strategy_id START 1;
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    exchange VARCHAR NOT NULL,
                    api_key_encrypted VARCHAR NOT NULL,
                    api_secret_encrypted VARCHAR NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    UNIQUE(user_id, exchange)
                );
                CREATE SEQUENCE IF NOT EXISTS seq_api_key_id START 1;
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action VARCHAR,
                    resource_type VARCHAR,
                    resource_id VARCHAR,
                    details VARCHAR,
                    ip_address VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_audit_id START 1;
            """)
            
            # Run migrations for existing tables
            try:
                # Add user_id column to trades table if it doesn't exist
                self.conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS user_id INTEGER")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
                logger.info("Trades table migration completed (user_id column)")
                
                # Add user_id column to backtest_results table if it doesn't exist
                self.conn.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS user_id INTEGER")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_user_id ON backtest_results(user_id)")
                logger.info("Backtest results table migration completed (user_id column)")
                
                # Add Telegram settings to users table if they don't exist
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_bot_token VARCHAR")
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR")
                logger.info("Users table migration completed (Telegram columns)")
            except Exception as migration_error:
                # Table might not exist yet, which is fine
                logger.info(f"Table migration skipped (table may not exist yet): {migration_error}")
            
            logger.info("Tables checked/created.")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    def save_result(self, result, user_id=None):
        """
        Saves a backtest result to the database.
        result: dict containing strategy, params, return, win_rate, trades, final_balance
        user_id: ID of the user who ran this backtest
        """
        try:
            timestamp = datetime.now()
            query = """
                INSERT INTO backtest_results 
                (id, timestamp, strategy, parameters, return_pct, win_rate_pct, trades, final_balance, user_id)
                VALUES (nextval('seq_backtest_id'), ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                timestamp,
                result['strategy'],
                str(result['params']),
                result['return'],
                result['win_rate'],
                result['trades'],
                result['final_balance'],
                user_id
            ])
            logger.info(f"Backtest result saved for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving result: {e}")

    def get_leaderboard(self, user_id=None):
        """Returns the leaderboard sorted by return, optionally filtered by user."""
        try:
            if user_id is not None:
                df = self.conn.execute(
                    "SELECT * FROM backtest_results WHERE user_id = ? ORDER BY return_pct DESC",
                    [user_id]
                ).fetchdf()
            else:
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

    def save_trade(self, trade_data, user_id=None):
        """
        Saves a trade to the database.
        trade_data: dict containing symbol, side, price, amount, type, pnl, strategy
        user_id: ID of the user who owns this trade
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
            try:
                self.conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS user_id INTEGER")
            except:
                pass
            try:
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
            except:
                pass
            
            query = """
                INSERT INTO trades 
                (id, timestamp, symbol, side, price, amount, total_value, type, pnl, strategy, leverage, user_id)
                VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                trade_data.get('leverage', 1.0),
                user_id
            ])
            logger.info(f"Trade saved: {trade_data['side']} {trade_data['symbol']} ({trade_data['type']}) for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving trade: {e}")

    def get_trades(self, limit=50, user_id=None):
        """Returns recent trades, optionally filtered by user_id."""
        try:
            # Check if table exists first
            tables = self.conn.execute("SHOW TABLES").fetchall()
            if ('trades',) not in tables:
                return pd.DataFrame()

            if user_id is not None:
                df = self.conn.execute(
                    f"SELECT * FROM trades WHERE user_id = ? ORDER BY timestamp DESC LIMIT {limit}",
                    [user_id]
                ).fetchdf()
            else:
                df = self.conn.execute(f"SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}").fetchdf()
            
            # Convert timestamp to string for JSON serialization
            if not df.empty:
                df['timestamp'] = df['timestamp'].astype(str)
            return df
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return pd.DataFrame()

    def clear_trades(self, user_id=None):
        """Deletes trades from the database, optionally filtered by user_id."""
        try:
            if user_id is not None:
                self.conn.execute("DELETE FROM trades WHERE user_id = ?", [user_id])
                logger.info(f"Cleared trades for user {user_id}")
            else:
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

    def get_total_pnl(self, user_id=None):
        """Returns the sum of PnL, optionally filtered by user_id."""
        try:
            # Check if table exists first
            tables = self.conn.execute("SHOW TABLES").fetchall()
            if ('trades',) not in tables:
                return 0.0
            
            # Sum pnl where it is not null
            if user_id is not None:
                result = self.conn.execute(
                    "SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL AND user_id = ?",
                    [user_id]
                ).fetchone()
            else:
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
        """Get user's strategy configuration."""
        try:
            result = self.conn.execute(
                "SELECT * FROM user_strategies WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
            
            import json
            return {
                "SYMBOL": result[2],
                "TIMEFRAME": result[3],
                "AMOUNT_USDT": result[4],
                "STRATEGY": result[5],
                "STRATEGY_PARAMS": json.loads(result[6]) if result[6] else {},
                "DRY_RUN": bool(result[7]),
                "TAKE_PROFIT_PCT": result[8],
                "STOP_LOSS_PCT": result[9]
            }
        except Exception as e:
            logger.error(f"Error fetching user strategy: {e}")
            return None

    def save_user_strategy(self, user_id, strategy_config):
        """Save user's strategy configuration."""
        try:
            import json
            from datetime import datetime
            
            # Check if strategy exists for this user
            existing = self.conn.execute(
                "SELECT id FROM user_strategies WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if existing:
                # Update existing
                query = """
                    UPDATE user_strategies 
                    SET symbol = ?, timeframe = ?, amount_usdt = ?, strategy = ?, 
                        strategy_params = ?, dry_run = ?, take_profit_pct = ?, 
                        stop_loss_pct = ?, updated_at = ?
                    WHERE user_id = ?
                """
                self.conn.execute(query, [
                    strategy_config.get("SYMBOL"),
                    strategy_config.get("TIMEFRAME"),
                    strategy_config.get("AMOUNT_USDT"),
                    strategy_config.get("STRATEGY"),
                    json.dumps(strategy_config.get("STRATEGY_PARAMS", {})),
                    strategy_config.get("DRY_RUN", True),
                    strategy_config.get("TAKE_PROFIT_PCT"),
                    strategy_config.get("STOP_LOSS_PCT"),
                    datetime.now(),
                    user_id
                ])
            else:
                # Insert new
                query = """
                    INSERT INTO user_strategies 
                    (id, user_id, symbol, timeframe, amount_usdt, strategy, strategy_params, 
                     dry_run, take_profit_pct, stop_loss_pct, updated_at)
                    VALUES (nextval('seq_user_strategy_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    strategy_config.get("SYMBOL"),
                    strategy_config.get("TIMEFRAME"),
                    strategy_config.get("AMOUNT_USDT"),
                    strategy_config.get("STRATEGY"),
                    json.dumps(strategy_config.get("STRATEGY_PARAMS", {})),
                    strategy_config.get("DRY_RUN", True),
                    strategy_config.get("TAKE_PROFIT_PCT"),
                    strategy_config.get("STOP_LOSS_PCT"),
                    datetime.now()
                ])
            
            logger.info(f"Saved strategy for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user strategy: {e}")
            return False

    def get_api_key(self, user_id, exchange):
        """Get user's encrypted API keys for an exchange."""
        try:
            result = self.conn.execute(
                "SELECT api_key_encrypted, api_secret_encrypted FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()
            
            if not result:
                return None
            
            return {
                'api_key_encrypted': result[0],
                'api_secret_encrypted': result[1]
            }
        except Exception as e:
            logger.error(f"Error fetching API key: {e}")
            return None

    def save_api_key(self, user_id, exchange, api_key_encrypted, api_secret_encrypted):
        """Save or update user's encrypted API keys for an exchange."""
        try:
            from datetime import datetime
            
            # Check if exists
            existing = self.conn.execute(
                "SELECT id FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()
            
            if existing:
                # Update
                query = """
                    UPDATE api_keys 
                    SET api_key_encrypted = ?, api_secret_encrypted = ?, updated_at = ?
                    WHERE user_id = ? AND exchange = ?
                """
                self.conn.execute(query, [
                    api_key_encrypted,
                    api_secret_encrypted,
                    datetime.now(),
                    user_id,
                    exchange
                ])
            else:
                # Insert
                query = """
                    INSERT INTO api_keys 
                    (id, user_id, exchange, api_key_encrypted, api_secret_encrypted, created_at, updated_at)
                    VALUES (nextval('seq_api_key_id'), ?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    exchange,
                    api_key_encrypted,
                    api_secret_encrypted,
                    datetime.now(),
                    datetime.now()
                ])
            
            logger.info(f"Saved API keys for user {user_id}, exchange {exchange}")
            return True
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
            return False

    def delete_api_key(self, user_id, exchange):
        """Delete user's API keys for an exchange."""
        try:
            self.conn.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            )
            logger.info(f"Deleted API keys for user {user_id}, exchange {exchange}")
            return True
        except Exception as e:
            logger.error(f"Error deleting API keys: {e}")
            return False

    def log_audit(self, user_id, action, resource_type, resource_id, details, ip_address=None):
        """Log an audit event."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO audit_log 
                (id, user_id, action, resource_type, resource_id, details, ip_address, created_at)
                VALUES (nextval('seq_audit_id'), ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                user_id,
                action,
                resource_type,
                resource_id,
                details,
                ip_address,
                datetime.now()
            ])
            return True
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return False
    
    def get_user_by_id(self, user_id):
        """Retrieve a user by their ID including Telegram settings."""
        try:
            result = self.conn.execute(
                "SELECT id, email, telegram_bot_token, telegram_chat_id FROM users WHERE id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'email': result[1],
                'telegram_bot_token': result[2],
                'telegram_chat_id': result[3]
            }
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
    
    def update_telegram_settings(self, user_id, bot_token, chat_id):
        """Update user's Telegram notification settings."""
        try:
            self.conn.execute(
                "UPDATE users SET telegram_bot_token = ?, telegram_chat_id = ? WHERE id = ?",
                [bot_token, chat_id, user_id]
            )
            logger.info(f"Updated Telegram settings for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating Telegram settings: {e}")
            return False


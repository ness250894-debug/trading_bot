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
                    user_id BIGINT
                );
                CREATE SEQUENCE IF NOT EXISTS seq_backtest_id START 1;
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    email VARCHAR UNIQUE,
                    hashed_password VARCHAR,
                    nickname VARCHAR,
                    telegram_bot_token VARCHAR,
                    telegram_chat_id VARCHAR,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_user_id START 1;
                CREATE TABLE IF NOT EXISTS user_strategies (
                    id INTEGER PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    symbol VARCHAR,
                    timeframe VARCHAR,
                    amount_usdt DOUBLE,
                    strategy VARCHAR,
                    strategy_params VARCHAR,
                    dry_run BOOLEAN,
                    take_profit_pct DOUBLE,
                    stop_loss_pct DOUBLE,
                    exchange VARCHAR DEFAULT 'bybit',
                    updated_at TIMESTAMP,
                    UNIQUE(user_id)
                );
                CREATE SEQUENCE IF NOT EXISTS seq_user_strategy_id START 1;
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY,
                    user_id BIGINT NOT NULL,
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
                    user_id BIGINT,
                    action VARCHAR,
                    resource_type VARCHAR,
                    resource_id VARCHAR,
                    details VARCHAR,
                    ip_address VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_audit_id START 1;
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    plan_id VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    starts_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    auto_renew BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP,
                    UNIQUE(user_id)
                );
                CREATE SEQUENCE IF NOT EXISTS seq_subscription_id START 1;
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    charge_code VARCHAR NOT NULL,
                    amount DOUBLE,
                    currency VARCHAR,
                    status VARCHAR,
                    plan_id VARCHAR,
                    created_at TIMESTAMP,
                    confirmed_at TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_payment_id START 1;
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    user_id BIGINT,
                    symbol VARCHAR,
                    side VARCHAR,
                    price DOUBLE,
                    amount DOUBLE,
                    type VARCHAR,
                    pnl DOUBLE,
                    strategy VARCHAR,
                    timestamp TIMESTAMP
                );
                CREATE SEQUENCE IF NOT EXISTS seq_trade_id START 1;
                CREATE TABLE IF NOT EXISTS plans (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    price DOUBLE NOT NULL,
                    currency VARCHAR NOT NULL,
                    duration_days INTEGER NOT NULL,
                    features TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
            """)
            
            # Run migrations for existing tables
            try:
                # Add user_id column to trades table if it doesn't exist
                self.conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS user_id BIGINT")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
                
                # Add user_id column to backtest_results table if it doesn't exist
                self.conn.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS user_id BIGINT")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_user_id ON backtest_results(user_id)")
                
                # Add Telegram settings to users table if they don't exist
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_bot_token VARCHAR")
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR")

                # Add is_admin column to users table if it doesn't exist
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
                
                # Add nickname column to users table if it doesn't exist
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR")
                
                # Add exchange column to user_strategies table if it doesn't exist
                self.conn.execute("ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS exchange VARCHAR DEFAULT 'bybit'")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_user_strategies_exchange ON user_strategies(exchange)")

                # Migration: Force convert INTEGER user_id columns to BIGINT by recreating tables
                # This is necessary because simple ALTER COLUMN might fail or not be supported for all cases
                tables_to_migrate = [
                    'user_strategies', 'api_keys', 'audit_log', 'subscriptions', 
                    'payments', 'trades', 'backtest_results', 'visual_strategies',
                    'public_strategies', 'strategy_clones'
                ]
                
                for table in tables_to_migrate:
                    try:
                        # Check if table exists
                        table_exists = self.conn.execute(
                            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", 
                            [table]
                        ).fetchone()[0] > 0
                        
                        if table_exists:
                            # Check column type - FIXED: Use parameterized query instead of f-string
                            col_type = self.conn.execute(
                                "SELECT data_type FROM information_schema.columns WHERE table_name = ? AND column_name = ?",
                                [table, 'user_id']
                            ).fetchone()
                            
                            if col_type and col_type[0] != 'BIGINT':
                                logger.info(f"Migrating {table} to BIGINT...")
                                # 1. Rename old table
                                # NOTE: Table names cannot be parameterized in DuckDB, but we control the table list
                                self.conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                                
                                # 2. Create new table with correct schema (we rely on the CREATE TABLE IF NOT EXISTS above, 
                                # but since we renamed the old one, we need to run the specific CREATE statement for this table)
                                # For simplicity, we'll just copy the structure with BIGINT
                                self.conn.execute(f"CREATE TABLE {table} AS SELECT * FROM {table}_old WHERE 1=0")
                                self.conn.execute(f"ALTER TABLE {table} ALTER COLUMN user_id TYPE BIGINT")
                                
                                # 3. Copy data
                                self.conn.execute(f"INSERT INTO {table} SELECT * FROM {table}_old")
                                
                                # 4. Drop old table
                                self.conn.execute(f"DROP TABLE {table}_old")
                                logger.info(f"Successfully migrated {table} to BIGINT")
                                
                    except Exception as e:
                        logger.error(f"Migration failed for {table}: {e}")
                        # Attempt to restore if stuck
                        try:
                            # NOTE: Table names cannot be parameterized, but we control the table name
                            self.conn.execute(f"ALTER TABLE {table}_old RENAME TO {table}")
                        except Exception as restore_error:
                            logger.error(f"Failed to restore table after migration: {restore_error}")

                # Create visual_strategies table for JSON-based strategies
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS visual_strategies (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name VARCHAR NOT NULL,
                        description TEXT,
                        json_config TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_visual_strategies_user_id ON visual_strategies(user_id)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_visual_strategy_id START 1")
                logger.info("Visual strategies table created successfully")
                
                # Create public_strategies table for social trading/marketplace
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS public_strategies (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        strategy_id INTEGER NOT NULL,
                        name VARCHAR NOT NULL,
                        description TEXT,
                        strategy_config TEXT NOT NULL,
                        performance_stats TEXT,
                        total_trades INTEGER DEFAULT 0,
                        win_rate DOUBLE DEFAULT 0,
                        total_pnl DOUBLE DEFAULT 0,
                        clones_count INTEGER DEFAULT 0,
                        rating DOUBLE DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(user_id, strategy_id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_public_strategies_rating ON public_strategies(rating DESC)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_public_strategies_pnl ON public_strategies(total_pnl DESC)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_public_strategy_id START 1")
                
                # Create strategy_clones tracking table
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_clones (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        public_strategy_id INTEGER NOT NULL,
                        cloned_strategy_id INTEGER NOT NULL,
                        cloned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (public_strategy_id) REFERENCES public_strategies(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_clones_user ON strategy_clones(user_id)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_clone_id START 1")
                
                logger.info("Social trading tables created successfully")
                
            except Exception as migration_error:
                # Table might not exist yet, which is fine
                logger.info(f"Table migration skipped (table may not exist yet): {migration_error}")
            
            # Migration: Add nickname column to existing users tables  
            try:
                self.conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR")
                logger.info("Migration: nickname column added/verified in users table")
            except Exception as e:
                logger.debug(f"Nickname migration: {e}")
            
            logger.info("Tables checked/created.")
            
            # Seed initial plans if empty
            try:
                count = self.conn.execute("SELECT count(*) FROM plans").fetchone()[0]
                if count == 0:
                    logger.info("Seeding initial plans...")
                    initial_plans = [
                        ('free_monthly', 'Free Monthly', 0, 'USD', 30, '["1 Active Bot", "Basic Strategies", "Paper Trading Only", "Community Support"]'),
                        ('free_yearly', 'Free Yearly', 0, 'USD', 365, '["1 Active Bot", "Basic Strategies", "Paper Trading Only", "Community Support"]'),
                        ('basic_monthly', 'Basic Monthly', 19, 'USD', 30, '["3 Active Bots", "Standard Strategies", "Live Trading", "Email Support"]'),
                        ('basic_yearly', 'Basic Yearly', 190, 'USD', 365, '["3 Active Bots", "Standard Strategies", "Live Trading", "Email Support"]'),
                        ('pro_monthly', 'Pro Monthly', 49, 'USD', 30, '["Unlimited Bots", "All Strategies", "Priority Support", "Advanced Analytics", "API Access"]'),
                        ('pro_yearly', 'Pro Yearly', 490, 'USD', 365, '["Unlimited Bots", "All Strategies", "Priority Support", "Advanced Analytics", "API Access"]'),
                        ('elite_monthly', 'Elite Monthly', 99, 'USD', 30, '["Everything in Pro", "1-on-1 Mentoring", "Custom Strategy Dev", "White Glove Support"]'),
                        ('elite_yearly', 'Elite Yearly', 990, 'USD', 365, '["Everything in Pro", "1-on-1 Mentoring", "Custom Strategy Dev", "White Glove Support"]')
                    ]
                    
                    for plan in initial_plans:
                        self.conn.execute(
                            "INSERT INTO plans (id, name, price, currency, duration_days, features, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                            plan
                        )
                    logger.info("Initial plans seeded.")
            except Exception as e:
                logger.error(f"Error seeding plans: {e}")

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
        """Clears the leaderboard."""
        try:
            self.conn.execute("DELETE FROM backtest_results")
            return True
        except Exception as e:
            logger.error(f"Error clearing leaderboard: {e}")
            return False

    def save_trade(self, user_id, symbol, side, amount, price, pnl=0):
        """Save a trade to the database."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO trades (id, user_id, symbol, side, amount, price, pnl, timestamp)
                VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, symbol, side, amount, price, pnl, datetime.now()])
            return True
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return False

    def get_trades(self, user_id, limit=100, offset=0):
        """Get trades for a user."""
        try:
            return self.conn.execute(
                "SELECT * FROM trades WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                [user_id, limit, offset]
            ).fetchdf()
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return pd.DataFrame()

    def get_total_pnl(self, user_id):
        """Get total PnL for a user."""
        try:
            result = self.conn.execute(
                "SELECT SUM(pnl) FROM trades WHERE user_id = ?",
                [user_id]
            ).fetchone()
            return result[0] if result and result[0] else 0.0
        except Exception as e:
            logger.error(f"Error calculating PnL: {e}")
            return 0.0

    def get_user_by_email(self, email):
        """Get user by email."""
        try:
            result = self.conn.execute(
                "SELECT * FROM users WHERE email = ?",
                [email]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'email': result[1],
                'hashed_password': result[2],
                'nickname': result[3] if len(result) > 3 else None,
                'telegram_bot_token': result[4] if len(result) > 4 else None,
                'telegram_chat_id': result[5] if len(result) > 5 else None,
                'is_admin': result[6] if len(result) > 6 else False,
                'created_at': result[7] if len(result) > 7 else None
            }
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    def create_user(self, email, hashed_password):
        """Create a new user."""
        try:
            from datetime import datetime
            # Check if user exists
            if self.get_user_by_email(email):
                return None
                
            query = """
                INSERT INTO users (id, email, hashed_password, is_active, is_admin, created_at)
                VALUES (nextval('seq_user_id'), ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [email, hashed_password, True, False, datetime.now()])
            return self.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_strategy(self, user_id):
        """Get strategy for a user."""
        try:
            import json
            result = self.conn.execute(
                "SELECT * FROM user_strategies WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'user_id': result[0],
                'strategy_name': result[1],
                'parameters': json.loads(result[2]) if result[2] else {},
                'is_active': result[3],
                'updated_at': result[4]
            }
        except Exception as e:
            logger.error(f"Error fetching strategy: {e}")
            return None

    def save_user_strategy(self, user_id, strategy_name, parameters, is_active=True):
        """Save or update user strategy."""
        try:
            import json
            from datetime import datetime
            
            # Check if exists
            existing = self.conn.execute(
                "SELECT 1 FROM user_strategies WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if existing:
                query = """
                    UPDATE user_strategies 
                    SET strategy_name = ?, parameters = ?, is_active = ?, updated_at = ?
                    WHERE user_id = ?
                """
                self.conn.execute(query, [
                    strategy_name,
                    json.dumps(parameters),
                    is_active,
                    datetime.now(),
                    user_id
                ])
            else:
                query = """
                    INSERT INTO user_strategies (user_id, strategy_name, parameters, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    strategy_name,
                    json.dumps(parameters),
                    is_active,
                    datetime.now()
                ])
            return True
        except Exception as e:
            logger.error(f"Error saving strategy: {e}")
            return False

    def get_api_key(self, user_id, exchange):
        """Get API key for user and exchange."""
        try:
            result = self.conn.execute(
                "SELECT * FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'user_id': result[1],
                'exchange': result[2],
                'api_key': result[3],
                'api_secret': result[4],
                'created_at': result[5]
            }
        except Exception as e:
            logger.error(f"Error fetching API key: {e}")
            return None

    def save_api_key(self, user_id, exchange, api_key, api_secret):
        """Save API key."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO api_keys (id, user_id, exchange, api_key, api_secret, created_at)
                VALUES (nextval('seq_api_key_id'), ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, exchange, api_key, api_secret, datetime.now()])
            return True
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False

    def delete_api_key(self, user_id, exchange):
        """Delete API key."""
        try:
            self.conn.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False

    def log_audit(self, user_id, action, details):
        """Log an audit event."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO audit_logs (id, user_id, action, details, timestamp)
                VALUES (nextval('seq_audit_id'), ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, action, details, datetime.now()])
            return True
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
            return False

    def get_user_by_id(self, user_id):
        """Get user by ID."""
        try:
            result = self.conn.execute(
                "SELECT * FROM users WHERE id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'email': result[1],
                'hashed_password': result[2],
                'nickname': result[3] if len(result) > 3 else None,
                'telegram_bot_token': result[4] if len(result) > 4 else None,
                'telegram_chat_id': result[5] if len(result) > 5 else None,
                'is_admin': result[6] if len(result) > 6 else False,
                'created_at': result[7] if len(result) > 7 else None
            }
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None

    def update_telegram_settings(self, user_id, chat_id):
        """Update user's Telegram chat ID."""
        try:
            self.conn.execute(
                "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
                [chat_id, user_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating Telegram settings: {e}")
            return False

    def update_user_nickname(self, user_id, nickname):
        """Update user's nickname."""
        try:
            self.conn.execute(
                "UPDATE users SET nickname = ? WHERE id = ?",
                [nickname, user_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating nickname: {e}")
            return False

    def create_subscription(self, user_id, plan_id, status, expires_at):
        """Create or update a user subscription."""
        try:
            from datetime import datetime
            # Check if subscription exists
            existing = self.conn.execute(
                "SELECT 1 FROM subscriptions WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if existing:
                query = """
                    UPDATE subscriptions 
                    SET plan_id = ?, status = ?, updated_at = ?, expires_at = ?
                    WHERE user_id = ?
                """
                self.conn.execute(query, [
                    plan_id,
                    status,
                    datetime.now(),
                    expires_at,
                    user_id
                ])
            else:
                query = """
                    INSERT INTO subscriptions (user_id, plan_id, status, created_at, expires_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    plan_id,
                    status,
                    datetime.now(),
                    expires_at,
                    datetime.now()
                ])
            return True
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return False

    def get_subscription(self, user_id):
        """Get user subscription."""
        try:
            result = self.conn.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'user_id': result[0],
                'plan_id': result[1],
                'status': result[2],
                'created_at': result[3],
                'expires_at': result[4],
                'updated_at': result[5]
            }
        except Exception as e:
            logger.error(f"Error fetching subscription: {e}")
            return None

    def create_payment(self, user_id, charge_code, amount, currency, plan_id):
        """Log a new payment attempt."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO payments 
                (id, user_id, charge_code, amount, currency, status, plan_id, created_at)
                VALUES (nextval('seq_payment_id'), ?, ?, ?, ?, 'created', ?, ?)
            """
            self.conn.execute(query, [
                user_id,
                charge_code,
                amount,
                currency,
                plan_id,
                datetime.now()
            ])
            return True
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return False

    def get_payment_by_charge_code(self, charge_code):
        """Get payment details by charge code."""
        try:
            result = self.conn.execute(
                "SELECT * FROM payments WHERE charge_code = ?",
                [charge_code]
            ).fetchone()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'user_id': result[1],
                'charge_code': result[2],
                'amount': result[3],
                'currency': result[4],
                'status': result[5],
                'plan_id': result[6],
                'created_at': result[7],
                'confirmed_at': result[8] if len(result) > 8 else None
            }
        except Exception as e:
            logger.error(f"Error fetching payment: {e}")
            return None

    def update_payment_status(self, charge_code, status):
        """Update payment status."""
        try:
            from datetime import datetime
            self.conn.execute(
                "UPDATE payments SET status = ?, confirmed_at = ? WHERE charge_code = ?",
                [status, datetime.now() if status == 'confirmed' else None, charge_code]
            )
            logger.info(f"Payment {charge_code} updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating payment: {e}")
            return False

    # Plan Management Methods
    
    def get_plans(self):
        """Get all active plans."""
        try:
            import json
            results = self.conn.execute("SELECT * FROM plans WHERE is_active = TRUE ORDER BY price ASC").fetchall()
            plans = []
            for r in results:
                plans.append({
                    'id': r[0],
                    'name': r[1],
                    'price': r[2],
                    'currency': r[3],
                    'duration_days': r[4],
                    'features': json.loads(r[5]) if r[5] else [],
                    'is_active': bool(r[6]),
                    'created_at': str(r[7]),
                    'updated_at': str(r[8])
                })
            return plans
        except Exception as e:
            logger.error(f"Error fetching plans: {e}")
            return []

    def get_plan(self, plan_id):
        """Get a specific plan."""
        try:
            import json
            result = self.conn.execute("SELECT * FROM plans WHERE id = ?", [plan_id]).fetchone()
            if not result:
                return None
            return {
                'id': result[0],
                'name': result[1],
                'price': result[2],
                'currency': result[3],
                'duration_days': result[4],
                'features': json.loads(result[5]) if result[5] else [],
                'is_active': bool(result[6]),
                'created_at': str(result[7]),
                'updated_at': str(result[8])
            }
        except Exception as e:
            logger.error(f"Error fetching plan: {e}")
            return None

    def create_plan(self, plan_data):
        """Create a new plan."""
        try:
            import json
            from datetime import datetime
            
            query = """
                INSERT INTO plans (id, name, price, currency, duration_days, features, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                plan_data['id'],
                plan_data['name'],
                plan_data['price'],
                plan_data['currency'],
                plan_data['duration_days'],
                json.dumps(plan_data.get('features', [])),
                plan_data.get('is_active', True),
                datetime.now(),
                datetime.now()
            ])
            logger.info(f"Plan created: {plan_data['id']}")
            return True
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return False

    def update_plan(self, plan_id, plan_data):
        """Update an existing plan."""
        try:
            import json
            from datetime import datetime
            
            # Build update query dynamically based on provided fields
            fields = []
            values = []
            
            if 'name' in plan_data:
                fields.append("name = ?")
                values.append(plan_data['name'])
            if 'price' in plan_data:
                fields.append("price = ?")
                values.append(plan_data['price'])
            if 'currency' in plan_data:
                fields.append("currency = ?")
                values.append(plan_data['currency'])
            if 'duration_days' in plan_data:
                fields.append("duration_days = ?")
                values.append(plan_data['duration_days'])
            if 'features' in plan_data:
                fields.append("features = ?")
                values.append(json.dumps(plan_data['features']))
            if 'is_active' in plan_data:
                fields.append("is_active = ?")
                values.append(plan_data['is_active'])
                
            fields.append("updated_at = ?")
            values.append(datetime.now())
            
            values.append(plan_id)
            
            query = f"UPDATE plans SET {', '.join(fields)} WHERE id = ?"
            self.conn.execute(query, values)
            logger.info(f"Plan updated: {plan_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating plan: {e}")
            return False

    def delete_plan(self, plan_id):
        """Delete (deactivate) a plan."""
        try:
            # We don't actually delete to preserve history, just deactivate
            self.conn.execute("UPDATE plans SET is_active = FALSE WHERE id = ?", [plan_id])
            return True
        except Exception as e:
            logger.error(f"Error deactivating plan: {e}")
            return False

    def get_all_users(self, skip: int = 0, limit: int = 100):
        """Get all users with their subscription status (with pagination)."""
        try:
            query = """
                SELECT u.id, u.email, u.nickname, u.created_at, u.is_admin, 
                       s.plan_id, s.status, s.expires_at
                FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id
                ORDER BY u.id DESC
                LIMIT ? OFFSET ?
            """
            df = self.conn.execute(query, [limit, skip]).fetchdf()
            
            # Convert timestamps to string
            if not df.empty:
                df['created_at'] = df['created_at'].astype(str)
                df['expires_at'] = df['expires_at'].astype(str)
                # Handle NaNs
                df = df.fillna('')
                
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    def update_user_subscription(self, user_id, plan_id, status):
        """Admin update of user subscription."""
        try:
            from datetime import datetime, timedelta
            
            # Set expiration based on plan (default 30 days if not specified)
            duration = 365 if 'yearly' in plan_id else 30
            expires_at = datetime.now() + timedelta(days=duration)
            
            return self.create_subscription(user_id, plan_id, status, expires_at)
        except Exception as e:
            logger.error(f"Error updating user subscription: {e}")
            return False

    def delete_user(self, user_id):
        """Delete a user and all their data."""
        try:
            # Delete related data first
            self.conn.execute("DELETE FROM subscriptions WHERE user_id = ?", [user_id])
            self.conn.execute("DELETE FROM user_strategies WHERE user_id = ?", [user_id])
            self.conn.execute("DELETE FROM api_keys WHERE user_id = ?", [user_id])
            self.conn.execute("DELETE FROM trades WHERE user_id = ?", [user_id])
            self.conn.execute("DELETE FROM backtest_results WHERE user_id = ?", [user_id])
            self.conn.execute("DELETE FROM payments WHERE user_id = ?", [user_id])
            
            # Delete user
            self.conn.execute("DELETE FROM users WHERE id = ?", [user_id])
            logger.info(f"Deleted user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    def set_admin_status(self, user_id, is_admin):
        """Set admin status for a user."""
        try:
            self.conn.execute(
                "UPDATE users SET is_admin = ? WHERE id = ?",
                [is_admin, user_id]
            )
            logger.info(f"Set admin status to {is_admin} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting admin status: {e}")
            return False


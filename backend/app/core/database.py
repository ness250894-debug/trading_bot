import duckdb
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Database")

import os

try:
    from .resilience import retry
except ImportError:
    # Fallback if resilience module not available
    def retry(max_attempts=3, delay=0.5, backoff=2):
        def decorator(func):
            return func
        return decorator

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
                    user_id BIGINT,
                    timeframe VARCHAR DEFAULT '1m',
                    symbol VARCHAR DEFAULT 'BTC/USDT'
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
                    position_start_time TIMESTAMP,
                    active_order_id VARCHAR,
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
                CREATE TABLE IF NOT EXISTS risk_profiles (
                    user_id BIGINT PRIMARY KEY,
                    max_daily_loss DOUBLE,
                    max_drawdown DOUBLE,
                    max_position_size DOUBLE,
                    max_open_positions INTEGER,
                    stop_trading_on_breach BOOLEAN DEFAULT TRUE,
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

                # Add state persistence columns to user_strategies
                self.conn.execute("ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS position_start_time TIMESTAMP")
                self.conn.execute("ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS active_order_id VARCHAR")

                # Migration: Force convert INTEGER user_id columns to BIGINT
                # Simplified approach: just use ALTER COLUMN directly since DuckDB supports it
                tables_to_migrate = [
                    'user_strategies', 'api_keys', 'audit_log', 'subscriptions', 
                    'payments', 'trades', 'backtest_results'
                ]
                
                for table in tables_to_migrate:
                    try:
                        # Check if table exists
                        table_exists = self.conn.execute(
                            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", 
                            [table]
                        ).fetchone()[0] > 0
                        
                        if table_exists:
                            # Check column type
                            col_type = self.conn.execute(
                                "SELECT data_type FROM information_schema.columns WHERE table_name = ? AND column_name = ?",
                                [table, 'user_id']
                            ).fetchone()
                            
                            if col_type and col_type[0] != 'BIGINT':
                                logger.info(f"Migrating {table}.user_id to BIGINT...")
                                # Simply alter the column type - DuckDB will handle the conversion
                                self.conn.execute(f"ALTER TABLE {table} ALTER COLUMN user_id TYPE BIGINT")
                                logger.info(f"Successfully migrated {table}.user_id to BIGINT")
                                
                    except Exception as e:
                        logger.warning(f"Migration skipped for {table}: {e}")


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

                # Performance Optimization: Add indexes for frequently queried columns
                logger.info("Creating performance indexes...")
                
                # Trades table indexes - optimize user queries and time-based filtering
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp ON trades(user_id, timestamp DESC)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)")
                
                # Backtest results indexes - optimize historical analysis
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_user_timestamp ON backtest_results(user_id, timestamp DESC)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results(strategy)")
                
                # Subscriptions indexes - optimize billing queries
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON subscriptions(expires_at)")
                
                # Payments indexes - optimize transaction history
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_charge ON payments(charge_code)")
                
                # API keys indexes - optimize key lookups
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_apikeys_user_exchange ON api_keys(user_id, exchange)")
                
                # Audit log indexes - optimize security monitoring
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(created_at DESC)")
                
                logger.info("Performance indexes created successfully")
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
                
                # Create bot_configurations table for multi-bot support
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_configurations (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        symbol VARCHAR NOT NULL,
                        strategy VARCHAR NOT NULL,
                        timeframe VARCHAR NOT NULL,
                        amount_usdt DOUBLE NOT NULL,
                        take_profit_pct DOUBLE NOT NULL,
                        stop_loss_pct DOUBLE NOT NULL,
                        parameters VARCHAR,
                        dry_run BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_configs_user ON bot_configurations(user_id)")
                self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_bot_configs_user_symbol ON bot_configurations(user_id, symbol)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_bot_config_id START 1")
                
                logger.info("Bot configurations table created successfully")
                
                # Create trade_notes table for Trade Journal
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS trade_notes (
                        id INTEGER PRIMARY KEY,
                        trade_id INTEGER NOT NULL,
                        user_id BIGINT NOT NULL,
                        notes TEXT,
                        tags VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trade_id) REFERENCES trades(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_notes_trade ON trade_notes(trade_id)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_notes_user ON trade_notes(user_id)")
                self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_notes_unique ON trade_notes(trade_id, user_id)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_trade_note_id START 1")
                
                logger.info("Trade notes table created successfully")
                
                # Create watchlists table
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS watchlists (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        symbol VARCHAR NOT NULL,
                        notes TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlists(user_id)")
                self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_symbol ON watchlists(user_id, symbol)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_watchlist_id START 1")
                
                logger.info("Watchlists table created successfully")
                
                # Create price_alerts table
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        symbol VARCHAR NOT NULL,
                        condition VARCHAR NOT NULL,
                        price_target DOUBLE NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        triggered_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON price_alerts(is_active)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_alert_id START 1")
                
                logger.info("Price alerts table created successfully")
                
                # Create dashboard_preferences table
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS dashboard_preferences (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL UNIQUE,
                        theme VARCHAR DEFAULT 'dark',
                        layout_config TEXT,
                        widgets_enabled TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prefs_user ON dashboard_preferences(user_id)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_pref_id START 1")
                
                logger.info("Dashboard preferences table created successfully")
                
                # Create backtest_templates table
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_templates (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name VARCHAR NOT NULL,
                        symbol VARCHAR NOT NULL,
                        timeframe VARCHAR NOT NULL,
                        strategy VARCHAR NOT NULL,
                        parameters TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_user ON backtest_templates(user_id)")
                self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_template_id START 1")
                
                logger.info("Backtest templates table created successfully")
                
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

    def save_result(self, result, user_id=None, timeframe='1m', symbol='BTC/USDT'):
        """
        Saves a backtest result to the database.
        result: dict containing strategy, params, return, win_rate, trades, final_balance
        user_id: ID of the user who ran this backtest
        timeframe: Timeframe used for the backtest (e.g., '1m', '5m', '1h')
        symbol: Symbol used for the backtest (e.g., 'BTC/USDT')
        """
        try:
            timestamp = datetime.now()
            query = """
                INSERT INTO backtest_results 
                (id, timestamp, strategy, parameters, return_pct, win_rate_pct, trades, final_balance, user_id, timeframe, symbol)
                VALUES (nextval('seq_backtest_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                timestamp,
                result['strategy'],
                str(result['params']),
                result['return'],
                result['win_rate'],
                result['trades'],
                result['final_balance'],
                user_id,
                timeframe,
                symbol
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

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade(self, user_id, symbol, side, amount, price, pnl=0):
        """Save a trade to the database."""
        from datetime import datetime
        query = """
            INSERT INTO trades (id, user_id, symbol, side, amount, price, pnl, timestamp)
            VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, [user_id, symbol, side, amount, price, pnl, datetime.now()])
        return True

    def get_trades(self, user_id, limit=100, offset=0):
        """Get trades for a user."""
        try:
            return self.conn.execute(
                """
                SELECT t.*, n.notes, n.tags 
                FROM trades t 
                LEFT JOIN trade_notes n ON t.id = n.trade_id 
                WHERE t.user_id = ? 
                ORDER BY t.timestamp DESC 
                LIMIT ? OFFSET ?
                """,
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

    def create_user(self, email, hashed_password, nickname=None):
        """Create a new user."""
        try:
            from datetime import datetime
            import random
            
            # Check if user exists
            if self.get_user_by_email(email):
                return None
            
            # Generate a unique 10-digit random ID
            max_attempts = 10
            for attempt in range(max_attempts):
                # Generate random 10-digit number (1000000000 to 9999999999)
                user_id = random.randint(1000000000, 9999999999)
                
                # Check if ID already exists
                existing = self.conn.execute(
                    "SELECT 1 FROM users WHERE id = ?",
                    [user_id]
                ).fetchone()
                
                if not existing:
                    # ID is unique, use it
                    break
            else:
                # Failed to generate unique ID after max_attempts
                logger.error("Failed to generate unique user ID after multiple attempts")
                return None
                
            query = """
                INSERT INTO users (id, email, hashed_password, nickname, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, email, hashed_password, nickname, False, datetime.now()])
            return self.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_strategy(self, user_id):
        """Get strategy configuration for a user."""
        try:
            import json
            result = self.conn.execute(
                "SELECT symbol, timeframe, amount_usdt, strategy, strategy_params, dry_run, take_profit_pct, stop_loss_pct, exchange, updated_at, position_start_time, active_order_id FROM user_strategies WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'SYMBOL': result[0],
                'TIMEFRAME': result[1],
                'AMOUNT_USDT': result[2],
                'STRATEGY': result[3],
                'STRATEGY_PARAMS': json.loads(result[4]) if result[4] else {},
                'DRY_RUN': result[5],
                'TAKE_PROFIT_PCT': result[6],
                'STOP_LOSS_PCT': result[7],
                'EXCHANGE': result[8] if result[8] else 'bybit',
                'updated_at': result[9],
                'position_start_time': result[10] if len(result) > 10 else None,
                'active_order_id': result[11] if len(result) > 11 else None
            }
        except Exception as e:
            logger.error(f"Error fetching strategy: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_user_strategy(self, user_id, config):
        """Save or update user strategy configuration.
        
        Args:
            user_id: The user's ID
            config: Dict with keys: SYMBOL, TIMEFRAME, AMOUNT_USDT, STRATEGY, STRATEGY_PARAMS, DRY_RUN, TAKE_PROFIT_PCT, STOP_LOSS_PCT
        """
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
                SET symbol = ?, timeframe = ?, amount_usdt = ?, strategy = ?, strategy_params = ?, 
                    dry_run = ?, take_profit_pct = ?, stop_loss_pct = ?, exchange = ?, updated_at = ?
                WHERE user_id = ?
            """
            self.conn.execute(query, [
                config.get('SYMBOL'),
                config.get('TIMEFRAME'),
                config.get('AMOUNT_USDT'),
                config.get('STRATEGY'),
                json.dumps(config.get('STRATEGY_PARAMS', {})),
                config.get('DRY_RUN', True),
                config.get('TAKE_PROFIT_PCT'),
                config.get('STOP_LOSS_PCT'),
                config.get('EXCHANGE', 'bybit'),
                datetime.now(),
                user_id
            ])
        else:
            query = """
                INSERT INTO user_strategies 
                (id, user_id, symbol, timeframe, amount_usdt, strategy, strategy_params, dry_run, take_profit_pct, stop_loss_pct, exchange, updated_at)
                VALUES (nextval('seq_user_strategy_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                user_id,
                config.get('SYMBOL'),
                config.get('TIMEFRAME'),
                config.get('AMOUNT_USDT'),
                config.get('STRATEGY'),
                json.dumps(config.get('STRATEGY_PARAMS', {})),
                config.get('DRY_RUN', True),
                config.get('TAKE_PROFIT_PCT'),
                config.get('STOP_LOSS_PCT'),
                config.get('EXCHANGE', 'bybit'),
                datetime.now()
            ])
        return True

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def update_bot_state(self, user_id, position_start_time=None, active_order_id=None):
        """Update bot state (start time, active order)."""
        from datetime import datetime
        
        updates = []
        params = []
        
        # We use a special string 'NO_CHANGE' to indicate no update
        if position_start_time != 'NO_CHANGE':
            updates.append("position_start_time = ?")
            params.append(position_start_time)
        
        if active_order_id != 'NO_CHANGE':
            updates.append("active_order_id = ?")
            params.append(active_order_id)
            
        if not updates:
            return True
            
        updates.append("updated_at = ?")
        params.append(datetime.now())
        
        params.append(user_id)
        
        query = f"UPDATE user_strategies SET {', '.join(updates)} WHERE user_id = ?"
        self.conn.execute(query, params)
        return True

    # Bot Configurations CRUD Methods
    def get_bot_configs(self, user_id):
        """Get all bot configurations for a user."""
        try:
            import json
            rows = self.conn.execute(
                "SELECT id, symbol, strategy, timeframe, amount_usdt, take_profit_pct, stop_loss_pct, parameters, dry_run, created_at, updated_at FROM bot_configurations WHERE user_id = ? ORDER BY created_at DESC",
                [user_id]
            ).fetchall()
            
            configs = []
            for row in rows:
                configs.append({
                    'id': row[0],
                    'symbol': row[1],
                    'strategy': row[2],
                    'timeframe': row[3],
                    'amount_usdt': row[4],
                    'take_profit_pct': row[5],
                    'stop_loss_pct': row[6],
                    'parameters': json.loads(row[7]) if row[7] else {},
                    'dry_run': row[8],
                    'created_at': row[9].isoformat() if row[9] else None,
                    'updated_at': row[10].isoformat() if row[10] else None
                })
            return configs
        except Exception as e:
            logger.error(f"Error fetching bot configs: {e}")
            return []

    def get_bot_config(self, user_id, config_id):
        """Get a specific bot configuration."""
        try:
            import json
            row = self.conn.execute(
                "SELECT id, symbol, strategy, timeframe, amount_usdt, take_profit_pct, stop_loss_pct, parameters, dry_run, created_at, updated_at FROM bot_configurations WHERE user_id = ? AND id = ?",
                [user_id, config_id]
            ).fetchone()
            
            if not row:
                return None
                
            return {
                'id': row[0],
                'symbol': row[1],
                'strategy': row[2],
                'timeframe': row[3],
                'amount_usdt': row[4],
                'take_profit_pct': row[5],
                'stop_loss_pct': row[6],
                'parameters': json.loads(row[7]) if row[7] else {},
                'dry_run': row[8],
                'created_at': row[9].isoformat() if row[9] else None,
                'updated_at': row[10].isoformat() if row[10] else None
            }
        except Exception as e:
            logger.error(f"Error fetching bot config: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_bot_config(self, user_id, config):
        """Create a new bot configuration.
        
        Args:
            user_id: User ID
            config: Dict with keys: symbol, strategy, timeframe, amount_usdt, take_profit_pct, stop_loss_pct, parameters (optional), dry_run
            
        Returns:
            Created config ID or None if failed
        """
        try:
            import json
            from datetime import datetime
            
            query = """
                INSERT INTO bot_configurations
                (id, user_id, symbol, strategy, timeframe, amount_usdt, take_profit_pct, stop_loss_pct, parameters, dry_run, created_at, updated_at)
                VALUES (nextval('seq_bot_config_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.conn.execute(query, [
                user_id,
                config.get('symbol'),
                config.get('strategy'),
                config.get('timeframe'),
                config.get('amount_usdt'),
                config.get('take_profit_pct'),
                config.get('stop_loss_pct'),
                json.dumps(config.get('parameters', {})),
                config.get('dry_run', True),
                datetime.now(),
                datetime.now()
            ])
            
            # Get the created config ID
            result = self.conn.execute(
                "SELECT id FROM bot_configurations WHERE user_id = ? AND symbol = ?",
                [user_id, config.get('symbol')]
            ).fetchone()
            
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating bot config: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def update_bot_config(self, user_id, config_id, config):
        """Update an existing bot configuration."""
        try:
            import json
            from datetime import datetime
            
            query = """
                UPDATE bot_configurations
                SET symbol = ?, strategy = ?, timeframe = ?, amount_usdt = ?,
                    take_profit_pct = ?, stop_loss_pct = ?, parameters = ?, dry_run = ?, updated_at = ?
                WHERE user_id = ? AND id = ?
            """
            
            self.conn.execute(query, [
                config.get('symbol'),
                config.get('strategy'),
                config.get('timeframe'),
                config.get('amount_usdt'),
                config.get('take_profit_pct'),
                config.get('stop_loss_pct'),
                json.dumps(config.get('parameters', {})),
                config.get('dry_run', True),
                datetime.now(),
                user_id,
                config_id
            ])
            return True
        except Exception as e:
            logger.error(f"Error updating bot config: {e}")
            return False

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_bot_config(self, user_id, config_id):
        """Delete a bot configuration."""
        try:
            self.conn.execute(
                "DELETE FROM bot_configurations WHERE user_id = ? AND id = ?",
                [user_id, config_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting bot config: {e}")
            return False

    # Trade Notes CRUD Methods
    def get_trade_note(self, user_id, trade_id):
        """Get note for a specific trade."""
        try:
            row = self.conn.execute(
                "SELECT id, trade_id, notes, tags, created_at, updated_at FROM trade_notes WHERE user_id = ? AND trade_id = ?",
                [user_id, trade_id]
            ).fetchone()
            
            if not row:
                return None
                
            return {
                'id': row[0],
                'trade_id': row[1],
                'notes': row[2],
                'tags': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None
            }
        except Exception as e:
            logger.error(f"Error fetching trade note: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade_note(self, user_id, trade_id, notes, tags=None):
        """Create or update a trade note.
        
        Args:
            user_id: User ID
            trade_id: Trade ID
            notes: Note content
            tags: Comma-separated tags (optional)
            
        Returns:
            Note ID or None if failed
        """
        try:
            from datetime import datetime
            
            # Check if note exists
            existing = self.conn.execute(
                "SELECT id FROM trade_notes WHERE user_id = ? AND trade_id = ?",
                [user_id, trade_id]
            ).fetchone()
            
            if existing:
                # Update existing note
                query = """
                    UPDATE trade_notes
                    SET notes = ?, tags = ?, updated_at = ?
                    WHERE user_id = ? AND trade_id = ?
                """
                self.conn.execute(query, [notes, tags, datetime.now(), user_id, trade_id])
                return existing[0]
            else:
                # Create new note
                query = """
                    INSERT INTO trade_notes
                    (id, trade_id, user_id, notes, tags, created_at, updated_at)
                    VALUES (nextval('seq_trade_note_id'), ?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [trade_id, user_id, notes, tags, datetime.now(), datetime.now()])
                
                # Get the created note ID
                result = self.conn.execute(
                    "SELECT id FROM trade_notes WHERE user_id = ? AND trade_id = ?",
                    [user_id, trade_id]
                ).fetchone()
                
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error saving trade note: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_trade_note(self, user_id, note_id):
        """Delete a trade note."""
        try:
            self.conn.execute(
                "DELETE FROM trade_notes WHERE user_id = ? AND id = ?",
                [user_id, note_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting trade note: {e}")
            return False

    # Watchlist CRUD Methods
    def get_watchlist(self, user_id):
        """Get user's watchlist."""
        try:
            rows = self.conn.execute(
                "SELECT id, symbol, notes, added_at FROM watchlists WHERE user_id = ? ORDER BY added_at DESC",
                [user_id]
            ).fetchall()
            
            watchlist = []
            for row in rows:
                watchlist.append({
                    'id': row[0],
                    'symbol': row[1],
                    'notes': row[2],
                    'added_at': row[3].isoformat() if row[3] else None
                })
            return watchlist
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
            return []

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def add_to_watchlist(self, user_id, symbol, notes=None):
        """Add symbol to watchlist."""
        try:
            from datetime import datetime
            
            query = """
                INSERT INTO watchlists
                (id, user_id, symbol, notes, added_at)
                VALUES (nextval('seq_watchlist_id'), ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, symbol, notes, datetime.now()])
            
            # Get the created watchlist item ID
            result = self.conn.execute(
                "SELECT id FROM watchlists WHERE user_id = ? AND symbol = ?",
                [user_id, symbol]
            ).fetchone()
            
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def remove_from_watchlist(self, user_id, symbol):
        """Remove symbol from watchlist."""
        try:
            self.conn.execute(
                "DELETE FROM watchlists WHERE user_id = ? AND symbol = ?",
                [user_id, symbol]
            )
            return True
        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            return False

    # Price Alerts CRUD Methods
    def get_alerts(self, user_id, active_only=True):
        """Get user's price alerts."""
        try:
            query = "SELECT id, symbol, condition, price_target, is_active, created_at, triggered_at FROM price_alerts WHERE user_id = ?"
            params = [user_id]
            
            if active_only:
                query += " AND is_active = TRUE"
            
            query += " ORDER BY created_at DESC"
            
            rows = self.conn.execute(query, params).fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'symbol': row[1],
                    'condition': row[2],
                    'price_target': row[3],
                    'is_active': row[4],
                    'created_at': row[5].isoformat() if row[5] else None,
                    'triggered_at': row[6].isoformat() if row[6] else None
                })
            return alerts
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_alert(self, user_id, symbol, condition, price_target):
        """Create a price alert.
        
        Args:
            user_id: User ID
            symbol: Trading pair
            condition: 'above' or 'below'
            price_target: Target price
        """
        try:
            from datetime import datetime
            
            query = """
                INSERT INTO price_alerts
                (id, user_id, symbol, condition, price_target, is_active, created_at)
                VALUES (nextval('seq_alert_id'), ?, ?, ?, ?, TRUE, ?)
            """
            self.conn.execute(query, [user_id, symbol, condition, price_target, datetime.now()])
            
            # Get created alert ID
            result = self.conn.execute(
                "SELECT CURRVAL('seq_alert_id')"
            ).fetchone()
            
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_alert(self, user_id, alert_id):
        """Delete a price alert."""
        try:
            self.conn.execute(
                "DELETE FROM price_alerts WHERE user_id = ? AND id = ?",
                [user_id, alert_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            return False

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def trigger_alert(self, alert_id):
        """Mark alert as triggered."""
        try:
            from datetime import datetime
            self.conn.execute(
                "UPDATE price_alerts SET is_active = FALSE, triggered_at = ? WHERE id = ?",
                [datetime.now(), alert_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
            return False

    # Dashboard Preferences CRUD Methods
    def get_preferences(self, user_id):
        """Get user's dashboard preferences."""
        try:
            import json
            row = self.conn.execute(
                "SELECT theme, layout_config, widgets_enabled, updated_at FROM dashboard_preferences WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not row:
                # Return default preferences
                return {
                    'theme': 'dark',
                    'layout_config': {},
                    'widgets_enabled': ['balance', 'status', 'trades', 'bots'],
                    'updated_at': None
                }
            
            return {
                'theme': row[0] or 'dark',
                'layout_config': json.loads(row[1]) if row[1] else {},
                'widgets_enabled': json.loads(row[2]) if row[2] else [],
                'updated_at': row[3].isoformat() if row[3] else None
            }
        except Exception as e:
            logger.error(f"Error fetching preferences: {e}")
            return {'theme': 'dark', 'layout_config': {}, 'widgets_enabled': []}

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_preferences(self, user_id, theme=None, layout_config=None, widgets_enabled=None):
        """Save user's dashboard preferences."""
        try:
            import json
            from datetime import datetime
            
            # Check if preferences exist
            existing = self.conn.execute(
                "SELECT 1 FROM dashboard_preferences WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if existing:
                # Build dynamic update
                updates = []
                params = []
                
                if theme is not None:
                    updates.append("theme = ?")
                    params.append(theme)
                
                if layout_config is not None:
                    updates.append("layout_config = ?")
                    params.append(json.dumps(layout_config))
                
                if widgets_enabled is not None:
                    updates.append("widgets_enabled = ?")
                    params.append(json.dumps(widgets_enabled))
                
                updates.append("updated_at = ?")
                params.append(datetime.now())
                params.append(user_id)
                
                if updates:
                    query = f"UPDATE dashboard_preferences SET {', '.join(updates)} WHERE user_id = ?"
                    self.conn.execute(query, params)
            else:
                # Create new preferences
                query = """
                    INSERT INTO dashboard_preferences
                    (id, user_id, theme, layout_config, widgets_enabled, updated_at)
                    VALUES (nextval('seq_pref_id'), ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    theme or 'dark',
                    json.dumps(layout_config or {}),
                    json.dumps(widgets_enabled or []),
                    datetime.now()
                ])
            
            return True
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            return False

    # Backtest Templates CRUD Methods
    def get_templates(self, user_id):
        """Get user's backtest templates."""
        try:
            import json
            rows = self.conn.execute(
                "SELECT id, name, symbol, timeframe, strategy, parameters, created_at FROM backtest_templates WHERE user_id = ? ORDER BY created_at DESC",
                [user_id]
            ).fetchall()
            
            templates = []
            for row in rows:
                templates.append({
                    'id': row[0],
                    'name': row[1],
                    'symbol': row[2],
                    'timeframe': row[3],
                    'strategy': row[4],
                    'parameters': json.loads(row[5]) if row[5] else {},
                    'created_at': row[6].isoformat() if row[6] else None
                })
            return templates
        except Exception as e:
            logger.error(f"Error fetching templates: {e}")
            return []

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_template(self, user_id, name, symbol, timeframe, strategy, parameters=None):
        """Create a backtest template."""
        try:
            import json
            from datetime import datetime
            
            query = """
                INSERT INTO backtest_templates
                (id, user_id, name, symbol, timeframe, strategy, parameters, created_at)
                VALUES (nextval('seq_template_id'), ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                user_id,
                name,
                symbol,
                timeframe,
                strategy,
                json.dumps(parameters or {}),
                datetime.now()
            ])
            
            # Get created template ID
            result = self.conn.execute(
                "SELECT CURRVAL('seq_template_id')"
            ).fetchone()
            
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_template(self, user_id, template_id):
        """Delete a backtest template."""
        try:
            self.conn.execute(
                "DELETE FROM backtest_templates WHERE user_id = ? AND id = ?",
                [user_id, template_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False

    def get_recent_trades(self, limit=10, user_id=None):
        """
        Fetch the most recent trades.
        Args:
            limit: Number of trades to return
            user_id: Optional user_id to filter by
        """
        try:
            query = "SELECT * FROM trades"
            params = []
            
            if user_id is not None:
                query += " WHERE user_id = ?"
                params.append(user_id)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Fetch as dictionary
            # Columns from trades table: id, user_id, symbol, side, price, amount, type, pnl, strategy, timestamp
            columns = ['id', 'user_id', 'symbol', 'side', 'price', 'amount', 'type', 'pnl', 'strategy', 'timestamp']
            
            rows = self.conn.execute(query, params).fetchall()
            
            trades = []
            for row in rows:
                trade = dict(zip(columns, row))
                trades.append(trade)
                
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []

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
                'api_key_encrypted': result[3],
                'api_secret_encrypted': result[4],
                'created_at': result[5],
                'updated_at': result[6] if len(result) > 6 else None
            }
        except Exception as e:
            logger.error(f"Error fetching API key: {e}")
            return None

    def save_api_key(self, user_id, exchange, api_key_encrypted, api_secret_encrypted):
        """Save encrypted API key."""
        try:
            from datetime import datetime
            
            # Check if key already exists
            existing = self.conn.execute(
                "SELECT 1 FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()
            
            if existing:
                # Update existing key
                query = """
                    UPDATE api_keys 
                    SET api_key_encrypted = ?, api_secret_encrypted = ?, updated_at = ?
                    WHERE user_id = ? AND exchange = ?
                """
                self.conn.execute(query, [api_key_encrypted, api_secret_encrypted, datetime.now(), user_id, exchange])
            else:
                # Insert new key
                query = """
                    INSERT INTO api_keys (id, user_id, exchange, api_key_encrypted, api_secret_encrypted, created_at, updated_at)
                    VALUES (nextval('seq_api_key_id'), ?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [user_id, exchange, api_key_encrypted, api_secret_encrypted, datetime.now(), datetime.now()])
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

    def log_audit(self, user_id, action, resource_type, resource_id, details, ip_address=None):
        """Log an audit event."""
        try:
            from datetime import datetime
            query = """
                INSERT INTO audit_log (id, user_id, action, resource_type, resource_id, details, ip_address, created_at)
                VALUES (nextval('seq_audit_id'), ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, action, resource_type, resource_id, details, ip_address, datetime.now()])
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
                    INSERT INTO subscriptions (id, user_id, plan_id, status, starts_at, expires_at, updated_at)
                    VALUES (nextval('seq_subscription_id'), ?, ?, ?, ?, ?, ?)
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
                'id': result[0],
                'user_id': result[1],
                'plan_id': result[2],
                'status': result[3],
                'starts_at': result[4],
                'expires_at': result[5],
                'updated_at': result[7] if len(result) > 7 else None
            }
        except Exception as e:
            logger.error(f"Error fetching subscription: {e}")
            return None
    
    def is_subscription_active(self, user_id):
        """Check if user has an active, non-expired subscription."""
        try:
            # Check if user is admin - admins bypass subscription checks
            user = self.get_user_by_id(user_id)
            if user and user.get('is_admin'):
                return True

            subscription = self.get_subscription(user_id)
            if not subscription:
                return False
            
            # Check status
            if subscription.get('status') != 'active':
                return False
            
            # Check expiration date
            from datetime import datetime
            expires_at = subscription.get('expires_at')
            if not expires_at:
                return False
                
            # Handle string dates from database
            if isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to parse expiration date '{expires_at}': {e}")
                    return False
            
            # Check if not expired
            return datetime.now() < expires_at
            
        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            # Fail-safe: allow trading if check fails to avoid blocking legitimate users
            return True

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

    def get_all_plans(self):
        """Get all plans (active and inactive)."""
        try:
            import json
            results = self.conn.execute("SELECT * FROM plans ORDER BY price ASC").fetchall()
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
            logger.error(f"Error fetching all plans: {e}")
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
            
    def get_risk_profile(self, user_id):
        """Get risk profile for a user."""
        try:
            result = self.conn.execute(
                "SELECT * FROM risk_profiles WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if result:
                return {
                    "user_id": result[0],
                    "max_daily_loss": result[1],
                    "max_drawdown": result[2],
                    "max_position_size": result[3],
                    "max_open_positions": result[4],
                    "stop_trading_on_breach": result[5],
                    "updated_at": result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching risk profile: {e}")
            return None

    def update_risk_profile(self, user_id, profile_data):
        """Update risk profile for a user."""
        try:
            # Check if profile exists
            existing = self.get_risk_profile(user_id)
            
            if existing:
                self.conn.execute(
                    """
                    UPDATE risk_profiles 
                    SET max_daily_loss = ?, max_drawdown = ?, max_position_size = ?, 
                        max_open_positions = ?, stop_trading_on_breach = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    [
                        profile_data.get('max_daily_loss'),
                        profile_data.get('max_drawdown'),
                        profile_data.get('max_position_size'),
                        profile_data.get('max_open_positions'),
                        profile_data.get('stop_trading_on_breach', True),
                        datetime.now(),
                        user_id
                    ]
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO risk_profiles (
                        user_id, max_daily_loss, max_drawdown, max_position_size, 
                        max_open_positions, stop_trading_on_breach, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        user_id,
                        profile_data.get('max_daily_loss'),
                        profile_data.get('max_drawdown'),
                        profile_data.get('max_position_size'),
                        profile_data.get('max_open_positions'),
                        profile_data.get('stop_trading_on_breach', True),
                        datetime.now()
                    ]
                )
            return True
        except Exception as e:
            logger.error(f"Error updating risk profile: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
                if logger:
                    logger.info("Database connection closed")
        except Exception as e:
            if logger:
                logger.error(f"Error closing database connection: {e}")
            else:
                print(f"Error closing database connection: {e}")
    
    def __del__(self):
        """Cleanup on garbage collection."""
        self.close()

# Global instance
db = DuckDBHandler()

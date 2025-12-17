-- Ensure Schema Updates for Legacy Databases
-- These columns were previously added via startup checks.
-- Listing them here ensures they are applied to any existing database.

-- Trades
ALTER TABLE trades ADD COLUMN IF NOT EXISTS user_id BIGINT;
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp ON trades(user_id, timestamp DESC);

-- Backtest Results
ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS user_id BIGINT;
ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS timeframe VARCHAR DEFAULT '1m';
ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS symbol VARCHAR DEFAULT 'BTC/USDT';
CREATE INDEX IF NOT EXISTS idx_backtest_user_id ON backtest_results(user_id);

-- Users
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR;

-- User Strategies
ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS exchange VARCHAR DEFAULT 'bybit';
ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS position_start_time TIMESTAMP;
ALTER TABLE user_strategies ADD COLUMN IF NOT EXISTS active_order_id VARCHAR;

-- Initial Schema Migration
-- Extracted from DuckDBHandler.create_tables

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

-- Visual Strategies
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
);
CREATE SEQUENCE IF NOT EXISTS seq_visual_strategy_id START 1;

-- Public Strategies
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
);
CREATE SEQUENCE IF NOT EXISTS seq_public_strategy_id START 1;

-- Strategy Clones
CREATE TABLE IF NOT EXISTS strategy_clones (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL,
    public_strategy_id INTEGER NOT NULL,
    cloned_strategy_id INTEGER NOT NULL,
    cloned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (public_strategy_id) REFERENCES public_strategies(id)
);
CREATE SEQUENCE IF NOT EXISTS seq_clone_id START 1;

-- Bot Configurations
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
);
CREATE SEQUENCE IF NOT EXISTS seq_bot_config_id START 1;

-- Trade Notes
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
);
CREATE SEQUENCE IF NOT EXISTS seq_trade_note_id START 1;

-- Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL,
    symbol VARCHAR NOT NULL,
    notes TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE SEQUENCE IF NOT EXISTS seq_watchlist_id START 1;

-- Price Alerts
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
);
CREATE SEQUENCE IF NOT EXISTS seq_alert_id START 1;

-- Dashboard Preferences
CREATE TABLE IF NOT EXISTS dashboard_preferences (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    theme VARCHAR DEFAULT 'dark',
    layout_config TEXT,
    widgets_enabled TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE SEQUENCE IF NOT EXISTS seq_pref_id START 1;

-- Backtest Templates
CREATE TABLE IF NOT EXISTS backtest_templates (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    timeframe VARCHAR NOT NULL,
    strategy VARCHAR NOT NULL,
    parameters TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE SEQUENCE IF NOT EXISTS seq_template_id START 1;

-- Trading Goals
CREATE TABLE IF NOT EXISTS trading_goals (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    target_amount DOUBLE NOT NULL,
    current_progress DOUBLE DEFAULT 0,
    target_date TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE SEQUENCE IF NOT EXISTS seq_goal_id START 1;

-- Exchanges
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    display_name VARCHAR NOT NULL,
    supports_futures BOOLEAN DEFAULT TRUE,
    supports_spot BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE SEQUENCE IF NOT EXISTS seq_exchange_id START 1;

-- Strategy Presets
CREATE TABLE IF NOT EXISTS strategy_presets (
    id INTEGER PRIMARY KEY,
    strategy_type VARCHAR NOT NULL,
    preset_name VARCHAR NOT NULL,
    parameters_json TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_type, preset_name)
);
CREATE SEQUENCE IF NOT EXISTS seq_strategy_preset_id START 1;

-- Risk Presets
CREATE TABLE IF NOT EXISTS risk_presets (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    take_profit_pct DOUBLE NOT NULL,
    stop_loss_pct DOUBLE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE SEQUENCE IF NOT EXISTS seq_risk_preset_id START 1;

-- Popular Symbols
CREATE TABLE IF NOT EXISTS popular_symbols (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR NOT NULL UNIQUE,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE SEQUENCE IF NOT EXISTS seq_popular_symbol_id START 1;

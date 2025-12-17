-- Add Indexes for Performance
-- Creating indexes on user_id for all user-specific tables to speed up queries and deletion.

CREATE INDEX IF NOT EXISTS idx_bot_configs_user_id ON bot_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_notes_user_id ON trade_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_price_alerts_user_id ON price_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_dash_prefs_user_id ON dashboard_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_goals_user_id ON trading_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_templates_user_id ON backtest_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_visual_strategies_user_id ON visual_strategies(user_id);

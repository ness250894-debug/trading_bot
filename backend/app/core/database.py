import duckdb
import pandas as pd
import logging
import os
import json
from datetime import datetime

# Repositories
from .repositories.user_repository import UserRepository
from .repositories.strategy_repository import StrategyRepository
from .repositories.trade_repository import TradeRepository
from .repositories.system_repository import SystemRepository
from .repositories.dashboard_repository import DashboardRepository
from .repositories.billing_repository import BillingRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Database")

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
        
        # Initialize Repositories
        self.user_repo = UserRepository(self.conn)
        self.strategy_repo = StrategyRepository(self.conn)
        self.trade_repo = TradeRepository(self.conn)
        self.system_repo = SystemRepository(self.conn)
        self.dashboard_repo = DashboardRepository(self.conn)
        self.billing_repo = BillingRepository(self.conn)
        
        from .repositories.auth_repository import AuthRepository
        self.auth_repo = AuthRepository(self.conn)

        # Run Migrations
        from .migration_manager import MigrationManager
        self.migration_manager = MigrationManager(self.conn)
        self.migration_manager.run_migrations()

    # ==========================================
    # DELEGATED METHODS
    # ==========================================

    # --- User Repository Delegates ---
    def get_user_by_email(self, email):
        return self.user_repo.get_user_by_email(email)

    def get_user_by_id(self, user_id):
        return self.user_repo.get_user_by_id(user_id)

    def create_user(self, email, hashed_password, nickname=None):
        return self.user_repo.create_user(email, hashed_password, nickname)

    def update_user_nickname(self, user_id, nickname):
        return self.user_repo.update_user_nickname(user_id, nickname)

    def update_telegram_settings(self, user_id, chat_id):
        return self.user_repo.update_telegram_settings(user_id, chat_id)

    def set_admin_status(self, user_id, is_admin):
        return self.user_repo.set_admin_status(user_id, is_admin)

    def delete_user(self, user_id):
        return self.user_repo.delete_user(user_id)

    def get_all_users(self, skip=0, limit=100):
        return self.user_repo.get_all_users(skip, limit)

    def get_api_key(self, user_id, exchange):
        return self.user_repo.get_api_key(user_id, exchange)

    def save_api_key(self, user_id, exchange, api_key_encrypted, api_secret_encrypted):
        return self.user_repo.save_api_key(user_id, exchange, api_key_encrypted, api_secret_encrypted)

    def get_risk_profile(self, user_id):
        return self.user_repo.get_risk_profile(user_id)

    def save_risk_profile(self, user_id, profile_data):
        return self.user_repo.save_risk_profile(user_id, profile_data)

    # --- Strategy Repository Delegates ---
    def get_user_strategy(self, user_id):
        return self.strategy_repo.get_user_strategy(user_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_user_strategy(self, user_id, config):
        return self.strategy_repo.save_user_strategy(user_id, config)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def update_bot_state(self, user_id, position_start_time=None, active_order_id=None):
        return self.strategy_repo.update_bot_state(user_id, position_start_time, active_order_id)

    def get_bot_configs(self, user_id):
        return self.strategy_repo.get_bot_configs(user_id)

    def get_bot_config(self, user_id, config_id):
        return self.strategy_repo.get_bot_config(user_id, config_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_bot_config(self, user_id, config):
        return self.strategy_repo.create_bot_config(user_id, config)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def update_bot_config(self, user_id, config_id, config):
        return self.strategy_repo.update_bot_config(user_id, config_id, config)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_bot_config(self, user_id, config_id):
        return self.strategy_repo.delete_bot_config(user_id, config_id)
        
    def save_result(self, result, user_id=None, timeframe='1m', symbol='BTC/USDT'):
        return self.strategy_repo.save_result(result, user_id, timeframe, symbol)

    def get_leaderboard(self, user_id=None):
        return self.strategy_repo.get_leaderboard(user_id)
        
    def clear_leaderboard(self):
        return self.strategy_repo.clear_leaderboard()

    # --- Trade Repository Delegates ---
    @retry(max_attempts=3, delay=0.5, backoff=2)
    def log_trade(self, trade_data):
        return self.trade_repo.log_trade(trade_data)
        
    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade(self, user_id, symbol, side, amount, price, pnl=0):
        return self.trade_repo.save_trade(user_id, symbol, side, amount, price, pnl)

    def get_trades(self, user_id, limit=50, offset=0):
        return self.trade_repo.get_trades(user_id, limit, offset)
        
    def get_recent_trades(self, limit=10, user_id=None):
        return self.trade_repo.get_recent_trades(limit, user_id)

    def get_total_pnl(self, user_id):
        return self.trade_repo.get_total_pnl(user_id)
        
    def get_daily_pnl(self, user_id):
        return self.trade_repo.get_daily_pnl(user_id)

    def get_trade_note(self, user_id, trade_id):
        return self.trade_repo.get_trade_note(user_id, trade_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade_note(self, user_id, trade_id, notes, tags=None):
        return self.trade_repo.save_trade_note(user_id, trade_id, notes, tags)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_trade_note(self, user_id, note_id):
        return self.trade_repo.delete_trade_note(user_id, note_id)

    # --- Billing Repository Delegates ---
    def create_subscription(self, user_id, plan_id, status, expires_at):
        return self.billing_repo.create_subscription(user_id, plan_id, status, expires_at)

    def get_subscription(self, user_id):
        return self.billing_repo.get_subscription(user_id)
        
    def is_subscription_active(self, user_id):
        return self.billing_repo.is_subscription_active(user_id)

    def create_payment(self, user_id, charge_code, amount, currency, plan_id):
        return self.billing_repo.create_payment(user_id, charge_code, amount, currency, plan_id)

    def get_payment_by_charge_code(self, charge_code):
        return self.billing_repo.get_payment_by_charge_code(charge_code)

    def update_payment_status(self, charge_code, status):
        return self.billing_repo.update_payment_status(charge_code, status)

    def get_plans(self):
        return self.billing_repo.get_plans()
        
    def get_all_plans(self):
        return self.billing_repo.get_all_plans()
        
    def get_plan(self, plan_id):
        return self.billing_repo.get_plan(plan_id)
        
    def create_plan(self, plan_data):
        return self.billing_repo.create_plan(plan_data)
        
    def update_plan(self, plan_id, plan_data):
        return self.billing_repo.update_plan(plan_id, plan_data)
        
    def delete_plan(self, plan_id):
        return self.billing_repo.delete_plan(plan_id)
        
    def update_user_subscription(self, user_id, plan_id, status):
        return self.billing_repo.update_user_subscription(user_id, plan_id, status)

    # --- System Repository Delegates ---
    def get_exchanges(self):
        return self.system_repo.get_exchanges()

    def get_strategy_presets(self, strategy_type=None):
        return self.system_repo.get_strategy_presets(strategy_type)

    def get_risk_presets(self):
        return self.system_repo.get_risk_presets()

    def get_popular_symbols(self):
        return self.system_repo.get_popular_symbols()

    # --- Dashboard Repository Delegates ---
    def get_watchlist(self, user_id):
        return self.dashboard_repo.get_watchlist(user_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def add_to_watchlist(self, user_id, symbol, notes=None):
        return self.dashboard_repo.add_to_watchlist(user_id, symbol, notes)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def remove_from_watchlist(self, user_id, symbol):
        return self.dashboard_repo.remove_from_watchlist(user_id, symbol)

    def get_alerts(self, user_id, active_only=True):
        return self.dashboard_repo.get_alerts(user_id, active_only)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_alert(self, user_id, symbol, condition, price_target):
        return self.dashboard_repo.create_alert(user_id, symbol, condition, price_target)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def delete_alert(self, user_id, alert_id):
        return self.dashboard_repo.delete_alert(user_id, alert_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def trigger_alert(self, alert_id):
        return self.dashboard_repo.trigger_alert(alert_id)

    def get_preferences(self, user_id):
        return self.dashboard_repo.get_preferences(user_id)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_preferences(self, user_id, theme=None, layout_config=None, widgets_enabled=None):
        return self.dashboard_repo.save_preferences(user_id, theme, layout_config, widgets_enabled)

    # --- Auth Repository Delegates ---
    def create_reset_token(self, user_id):
        return self.auth_repo.create_reset_token(user_id)

    def verify_reset_token(self, token):
        return self.auth_repo.verify_reset_token(token)

    def consume_reset_token(self, token):
        return self.auth_repo.consume_reset_token(token)

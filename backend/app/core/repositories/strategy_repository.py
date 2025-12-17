from .base import BaseRepository
from datetime import datetime
import json
from app.core.resilience import retry

class StrategyRepository(BaseRepository):
    def get_user_strategy(self, user_id):
        """Get strategy configuration for a user."""
        try:
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
            self.logger.error(f"Error fetching strategy: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_user_strategy(self, user_id, config):
        """Save or update user strategy configuration."""
        
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
            self.logger.error(f"Error fetching bot configs: {e}")
            return []

    def get_bot_config(self, user_id, config_id):
        """Get a specific bot configuration."""
        try:
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
            self.logger.error(f"Error fetching bot config: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_bot_config(self, user_id, config):
        """Create a new bot configuration."""
        try:
            # Use RETURNING id to get the ID of the inserted row
            query = """
                INSERT INTO bot_configurations
                (id, user_id, symbol, strategy, timeframe, amount_usdt, take_profit_pct, stop_loss_pct, parameters, dry_run, created_at, updated_at)
                VALUES (nextval('seq_bot_config_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """
            
            result = self.conn.execute(query, [
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
            ]).fetchone()
            
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error creating bot config: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def update_bot_config(self, user_id, config_id, config):
        """Update an existing bot configuration."""
        try:
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
            self.logger.error(f"Error updating bot config: {e}")
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
            self.logger.error(f"Error deleting bot config: {e}")
            return False

    # Backtest Result Methods
    def save_result(self, result, user_id=None, timeframe='1m', symbol='BTC/USDT'):
        """
        Saves a backtest result to the database.
        result: dict containing strategy, params, return, win_rate, trades, final_balance
        user_id: ID of the user who ran this backtest
        timeframe: Timeframe used for the backtest
        symbol: Symbol used for the backtest
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
            self.logger.info(f"Backtest result saved for user {user_id}")
        except Exception as e:
            self.logger.error(f"Error saving result: {e}")

    def get_leaderboard(self, user_id=None):
        """Returns the leaderboard sorted by return, optionally filtered by user."""
        try:
            import pandas as pd
            if user_id is not None:
                df = self.conn.execute(
                    "SELECT * FROM backtest_results WHERE user_id = ? ORDER BY return_pct DESC",
                    [user_id]
                ).fetchdf()
            else:
                df = self.conn.execute("SELECT * FROM backtest_results ORDER BY return_pct DESC").fetchdf()
            return df
        except Exception as e:
            self.logger.error(f"Error fetching leaderboard: {e}")
            import pandas as pd
            return pd.DataFrame()

    def clear_leaderboard(self):
        """Clears the leaderboard."""
        try:
            self.conn.execute("DELETE FROM backtest_results")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing leaderboard: {e}")
            return False

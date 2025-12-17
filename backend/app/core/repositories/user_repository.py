from .base import BaseRepository
from datetime import datetime
import random

class UserRepository(BaseRepository):
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
            self.logger.error(f"Error fetching user: {e}")
            return None

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
            self.logger.error(f"Error fetching user by ID: {e}")
            return None

    def create_user(self, email, hashed_password, nickname=None):
        """Create a new user."""
        try:
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
                self.logger.error("Failed to generate unique user ID after multiple attempts")
                return None
                
            query = """
                INSERT INTO users (id, email, hashed_password, nickname, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [user_id, email, hashed_password, nickname, False, datetime.now()])
            return self.get_user_by_email(email)
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return None

    def update_user_nickname(self, user_id, nickname):
        """Update user's nickname."""
        try:
            self.conn.execute(
                "UPDATE users SET nickname = ? WHERE id = ?",
                [nickname, user_id]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error updating nickname: {e}")
            return False

    def update_telegram_settings(self, user_id, chat_id):
        """Update user's Telegram chat ID."""
        try:
            self.conn.execute(
                "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
                [chat_id, user_id]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error updating Telegram settings: {e}")
            return False

    def set_admin_status(self, user_id, is_admin):
        """Set admin status for a user."""
        try:
            self.conn.execute(
                "UPDATE users SET is_admin = ? WHERE id = ?",
                [is_admin, user_id]
            )
            self.logger.info(f"Set admin status to {is_admin} for user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting admin status: {e}")
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
            self.logger.info(f"Deleted user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}")
            return False
            
    def get_all_users(self, skip=0, limit=100):
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
            self.logger.error(f"Error fetching all users: {e}")
            return []

    def get_api_key(self, user_id, exchange):
        """Get API keys for a user and exchange."""
        try:
            result = self.conn.execute(
                "SELECT api_key_encrypted, api_secret_encrypted FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()
            
            if result:
                return {
                    'api_key_encrypted': result[0],
                    'api_secret_encrypted': result[1]
                }
            return None
        except Exception as e:
            self.logger.error(f"Error fetching API key: {e}")
            return None

    def save_api_key(self, user_id, exchange, api_key_encrypted, api_secret_encrypted):
        """Save or update API keys."""
        try:
            # Check if exists
            existing = self.conn.execute(
                "SELECT 1 FROM api_keys WHERE user_id = ? AND exchange = ?",
                [user_id, exchange]
            ).fetchone()

            if existing:
                self.conn.execute(
                    """UPDATE api_keys 
                       SET api_key_encrypted = ?, api_secret_encrypted = ?, updated_at = ? 
                       WHERE user_id = ? AND exchange = ?""",
                    [api_key_encrypted, api_secret_encrypted, datetime.now(), user_id, exchange]
                )
            else:
                self.conn.execute(
                    """INSERT INTO api_keys (user_id, exchange, api_key_encrypted, api_secret_encrypted, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [user_id, exchange, api_key_encrypted, api_secret_encrypted, datetime.now(), datetime.now()]
                )
            return True
        except Exception as e:
            self.logger.error(f"Error saving API key: {e}")
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
                    'user_id': result[0],
                    'max_daily_loss': result[1],
                    'max_drawdown': result[2],
                    'max_position_size': result[3],
                    'max_open_positions': result[4],
                    'stop_trading_on_breach': result[5],
                    'updated_at': result[6]
                }
            return None
        except Exception as e:
            self.logger.error(f"Error fetching risk profile: {e}")
            return None

    def save_risk_profile(self, user_id, profile_data):
        """Save or update risk profile."""
        try:
            existing = self.conn.execute("SELECT 1 FROM risk_profiles WHERE user_id = ?", [user_id]).fetchone()
            
            if existing:
                query = """
                    UPDATE risk_profiles SET 
                    max_daily_loss=?, max_drawdown=?, max_position_size=?, 
                    max_open_positions=?, stop_trading_on_breach=?, updated_at=?
                    WHERE user_id=?
                """
                params = [
                    profile_data.get('max_daily_loss'),
                    profile_data.get('max_drawdown'),
                    profile_data.get('max_position_size'),
                    profile_data.get('max_open_positions'),
                    profile_data.get('stop_trading_on_breach', True),
                    datetime.now(),
                    user_id
                ]
            else:
                query = """
                    INSERT INTO risk_profiles 
                    (user_id, max_daily_loss, max_drawdown, max_position_size, max_open_positions, stop_trading_on_breach, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    user_id,
                    profile_data.get('max_daily_loss'),
                    profile_data.get('max_drawdown'),
                    profile_data.get('max_position_size'),
                    profile_data.get('max_open_positions'),
                    profile_data.get('stop_trading_on_breach', True),
                    datetime.now()
                ]
            self.conn.execute(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error saving risk profile: {e}")
            return False

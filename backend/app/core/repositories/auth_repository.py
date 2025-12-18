import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger("AuthRepository")

class AuthRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_reset_token(self, user_id):
        """Creates a password reset token valid for 15 minutes."""
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=15)
        
        try:
            self.conn.execute(
                "INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
                [token, user_id, expires_at]
            )
            return token
        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            return None

    def verify_reset_token(self, token):
        """Verifies if the token is valid and returns the user_id."""
        result = self.conn.execute(
            "SELECT user_id, expires_at, used FROM password_reset_tokens WHERE token = ?",
            [token]
        ).fetchone()

        if not result:
            return None
        
        user_id, expires_at, used = result
        
        if used:
            return None
            
        if datetime.now() > expires_at:
            return None
            
        return user_id

    def consume_reset_token(self, token):
        """Marks a token as used."""
        try:
            self.conn.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE token = ?",
                [token]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to consume token: {e}")
            return False

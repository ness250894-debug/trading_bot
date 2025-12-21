import duckdb
import os
import logging
try:
    from app.core.resilience import retry
except ImportError:
    # Fallback if resilience module not available or circular import issues
    def retry(max_attempts=3, delay=0.5, backoff=2):
        def decorator(func):
            return func
        return decorator

class BaseRepository:
    def __init__(self, conn):
        """
        Initialize with an existing DuckDB connection.
        
        Args:
            conn: An active DuckDB connection object.
        """
        self.conn = conn
        self.logger = logging.getLogger(self.__class__.__name__)

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def execute(self, query, params=None):
        """Execute a query with retry logic."""
        try:
            if params:
                return self.conn.execute(query, params)
            return self.conn.execute(query)
        except Exception as e:
            self.logger.error(f"Database error executing query: {query} with params {params}. Error: {e}")
            raise e

    def log_audit(self, user_id, action, resource_type, resource_id=None, details=None, ip_address=None):
        """Log an audit event."""
        try:
            from datetime import datetime
            self.conn.execute(
                """
                INSERT INTO audit_log (id, user_id, action, resource_type, resource_id, details, ip_address, created_at)
                VALUES (nextval('seq_audit_id'), ?, ?, ?, ?, ?, ?, ?)
                """,
                [user_id, action, resource_type, resource_id, details, ip_address, datetime.now()]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
            return False

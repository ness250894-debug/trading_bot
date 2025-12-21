from .base import BaseRepository
from datetime import datetime
import json
from app.core.resilience import retry

class DashboardRepository(BaseRepository):
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
            self.logger.error(f"Error fetching watchlist: {e}")
            return []

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def add_to_watchlist(self, user_id, symbol, notes=None):
        """Add symbol to watchlist."""
        try:
            # Validate symbol against supported list
            # We allow it if it exists in supported_symbols AND is active
            valid = self.conn.execute(
                "SELECT 1 FROM supported_symbols WHERE symbol = ? AND is_active = TRUE",
                [symbol]
            ).fetchone()
            
            if not valid:
                return None, f"Symbol '{symbol}' is not supported or invalid."
            
            # Remove existing entry if any (Overwrite behavior)
            self.conn.execute(
                "DELETE FROM watchlists WHERE user_id = ? AND symbol = ?",
                [user_id, symbol]
            )
            
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
            
            val = result[0] if result else None
            return val, None
        except Exception as e:
            self.logger.error(f"Error adding to watchlist: {e}")
            return None, str(e)


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
            self.logger.error(f"Error removing from watchlist: {e}")
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
            self.logger.error(f"Error fetching alerts: {e}")
            return []

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def create_alert(self, user_id, symbol, condition, price_target):
        """Create a price alert."""
        try:
            # Validate symbol
            valid = self.conn.execute(
                "SELECT 1 FROM supported_symbols WHERE symbol = ? AND is_active = TRUE",
                [symbol]
            ).fetchone()
            
            if not valid:
                return None, f"Symbol '{symbol}' is not supported."
            
            # Check for existing identical alert (Same Symbol, Condition, AND Price)
            # If exists, delete it (overwrite behavior) to bump it or update hidden fields if any
            self.conn.execute(
                """
                DELETE FROM price_alerts 
                WHERE user_id = ? 
                AND symbol = ? 
                AND condition = ? 
                AND price_target = ?
                """,
                [user_id, symbol, condition, price_target]
            )
                
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
            
            val = result[0] if result else None
            return val, None
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return None, str(e)



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
            self.logger.error(f"Error deleting alert: {e}")
            return False

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def trigger_alert(self, alert_id):
        """Mark alert as triggered."""
        try:
            self.conn.execute(
                "UPDATE price_alerts SET is_active = FALSE, triggered_at = ? WHERE id = ?",
                [datetime.now(), alert_id]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
            return False

    # Dashboard Preferences CRUD Methods
    def get_preferences(self, user_id):
        """Get user's dashboard preferences."""
        try:
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
            self.logger.error(f"Error fetching preferences: {e}")
            return {'theme': 'dark', 'layout_config': {}, 'widgets_enabled': []}

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_preferences(self, user_id, theme=None, layout_config=None, widgets_enabled=None):
        """Save user's dashboard preferences."""
        try:
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
            self.logger.error(f"Error saving preferences: {e}")
            return False

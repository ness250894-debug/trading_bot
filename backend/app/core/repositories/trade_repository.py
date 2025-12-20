from .base import BaseRepository
from datetime import datetime
from app.core.resilience import retry

class TradeRepository(BaseRepository):
    @retry(max_attempts=3, delay=0.5, backoff=2)
    def log_trade(self, trade_data):
        """Log a trade execution."""
        try:
            query = """
                INSERT INTO trades (id, user_id, symbol, side, price, amount, type, pnl, strategy, timestamp)
                VALUES (nextval('seq_trade_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                trade_data['user_id'],
                trade_data['symbol'],
                trade_data['side'],
                trade_data['price'],
                trade_data['amount'],
                trade_data['type'],
                trade_data.get('pnl', 0.0),
                trade_data.get('strategy', 'manual'),
                datetime.now()
            ])
            return True
        except Exception as e:
            self.logger.error(f"Error logging trade: {e}")
            return False

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade(self, user_id, symbol, side, amount, price, pnl=0):
        """Save a trade to the database (legacy compatibility)."""
        return self.log_trade({
            'user_id': user_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'type': 'market', # Default for simplified save
            'strategy': 'manual'
        })

    def get_trades(self, user_id, limit=50, offset=0):
        """Get recent trades for a user."""
        try:
            result = self.conn.execute(
                "SELECT id, user_id, symbol, side, price, amount, type, pnl, strategy, timestamp FROM trades WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                [user_id, limit, offset]
            ).fetchall()
            
            return self.transform_trade_data(result)
        except Exception as e:
            self.logger.error(f"Error fetching trades: {e}")
            return []
            
    def get_recent_trades(self, limit=10, user_id=None):
        """
        Fetch the most recent trades.
        Args:
            limit: Number of trades to return
            user_id: Optional user_id to filter by
        """
        try:
            query = "SELECT id, user_id, symbol, side, price, amount, type, pnl, strategy, timestamp FROM trades"
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
            self.logger.error(f"Error fetching recent trades: {e}")
            return []

    def transform_trade_data(self, rows):
        """Transform raw DB rows into trade dictionaries."""
        # Re-implementing transform for safety based on `get_recent_trades` columns
        columns = ['id', 'user_id', 'symbol', 'side', 'price', 'amount', 'type', 'pnl', 'strategy', 'timestamp']
        # Note: 'SELECT *' return order depends on table creation order.
        # Assuming standard order:
        # Based on INSERT in log_trade: id, user_id, symbol, side, price, amount, type, pnl, strategy, timestamp
        
        final_trades = []
        for row in rows:
            # If row length matches columns, map them
            if len(row) == len(columns):
                trade = dict(zip(columns, row))
                # Format timestamp
                if isinstance(trade['timestamp'], datetime):
                    trade['timestamp'] = trade['timestamp'].isoformat()
                final_trades.append(trade)
            else:
                # Fallback if schema differs (e.g. legacy data)
                self.logger.warning(f"Trade row length {len(row)} does not match expected {len(columns)}")
        
        return final_trades

    def get_total_pnl(self, user_id):
        """Get total PnL for a user."""
        try:
            result = self.conn.execute(
                "SELECT SUM(pnl) FROM trades WHERE user_id = ?",
                [user_id]
            ).fetchone()
            return result[0] if result and result[0] else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating PnL: {e}")
            return 0.0

    def get_daily_pnl(self, user_id):
        """Get total realized PnL for the current day (UTC)."""
        try:
            # DuckDB's current_date returns the start of the current day
            result = self.conn.execute(
                "SELECT SUM(pnl) FROM trades WHERE user_id = ? AND timestamp >= current_date",
                [user_id]
            ).fetchone()
            return result[0] if result and result[0] else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating daily PnL: {e}")
            return 0.0

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
            self.logger.error(f"Error fetching trade note: {e}")
            return None

    @retry(max_attempts=3, delay=0.5, backoff=2)
    def save_trade_note(self, user_id, trade_id, notes, tags=None):
        """Create or update a trade note."""
        try:
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
            self.logger.error(f"Error saving trade note: {e}")
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
            self.logger.error(f"Error deleting trade note: {e}")
            return False

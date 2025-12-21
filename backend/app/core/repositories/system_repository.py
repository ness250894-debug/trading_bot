from .base import BaseRepository
import json

class SystemRepository(BaseRepository):
    def get_exchanges(self):
        """Get all active exchanges."""
        try:
            rows = self.conn.execute(
                "SELECT id, name, display_name, supports_futures, supports_spot FROM exchanges WHERE is_active = TRUE ORDER BY name"
            ).fetchall()
            
            exchanges = []
            for row in rows:
                exchanges.append({
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'supports_futures': row[3],
                    'supports_spot': row[4]
                })
            return exchanges
        except Exception as e:
            self.logger.error(f"Error fetching exchanges: {e}")
            return []

    def get_strategy_presets(self, strategy_type=None):
        """Get strategy presets, optionally filtered by strategy type."""
        try:
            if strategy_type:
                rows = self.conn.execute(
                    "SELECT id, strategy_type, preset_name, parameters_json, description FROM strategy_presets WHERE strategy_type = ? AND is_active = TRUE ORDER BY preset_name",
                    [strategy_type]
                ).fetchall()
            else:
                rows = self.conn.execute(
                    "SELECT id, strategy_type, preset_name, parameters_json, description FROM strategy_presets WHERE is_active = TRUE ORDER BY strategy_type, preset_name"
                ).fetchall()
            
            presets = []
            for row in rows:
                presets.append({
                    'id': row[0],
                    'strategy_type': row[1],
                    'preset_name': row[2],
                    'parameters': json.loads(row[3]),
                    'description': row[4]
                })
            return presets
        except Exception as e:
            self.logger.error(f"Error fetching strategy presets: {e}")
            return []

    def get_risk_presets(self):
        """Get all active risk presets."""
        try:
            rows = self.conn.execute(
                "SELECT id, name, take_profit_pct, stop_loss_pct, description FROM risk_presets WHERE is_active = TRUE ORDER BY name"
            ).fetchall()
            
            presets = []
            for row in rows:
                presets.append({
                    'id': row[0],
                    'name': row[1],
                    'take_profit_pct': row[2],
                    'stop_loss_pct': row[3],
                    'description': row[4]
                })
            return presets
        except Exception as e:
            self.logger.error(f"Error fetching risk presets: {e}")
            return []

    def get_popular_symbols(self):
        """Get all active popular symbols."""
        try:
            rows = self.conn.execute(
                "SELECT id, symbol FROM popular_symbols WHERE is_active = TRUE ORDER BY display_order, symbol"
            ).fetchall()
            
            symbols = []
            for row in rows:
                symbols.append({
                    'id': row[0],
                    'symbol': row[1]
                })
            return symbols
        except Exception as e:
            self.logger.error(f"Error fetching popular symbols: {e}")
            return []

    def get_all_supported_symbols(self, exchange='bybit'):
        """Get all supported symbols representing valid pairs."""
        try:
            rows = self.conn.execute(
                "SELECT symbol FROM supported_symbols WHERE is_active = TRUE AND exchange = ? ORDER BY symbol ASC",
                [exchange]
            ).fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching supported symbols: {e}")
            return []

    def update_supported_symbols(self, symbols, exchange='bybit'):
        """
        Sync supported symbols. 
        Marks missing ones as inactive. 
        Adds new ones.
        """
        try:
            from datetime import datetime
            now = datetime.now()
            
            # 1. Get existing
            existing_rows = self.conn.execute(
                "SELECT symbol FROM supported_symbols WHERE exchange = ?",
                [exchange]
            ).fetchall()
            existing_set = set(row[0] for row in existing_rows)
            new_set = set(symbols)
            
            # 2. Add New
            to_add = new_set - existing_set
            for symbol in to_add:
                self.conn.execute(
                    "INSERT INTO supported_symbols (id, symbol, exchange, is_active, last_seen_at) VALUES (nextval('seq_supported_symbol_id'), ?, ?, TRUE, ?)",
                    [symbol, exchange, now]
                )
                
            # 3. Update Existing (mark active and touch timestamp)
            # Use chunks if list is huge, but for ~1000 symbols it's fine to iterate
            for symbol in new_set:
                self.conn.execute(
                    "UPDATE supported_symbols SET is_active = TRUE, last_seen_at = ? WHERE symbol = ? AND exchange = ?",
                    [now, symbol, exchange]
                )
                
            # 4. Mark removed as inactive
            to_deactivate = existing_set - new_set
            for symbol in to_deactivate:
                self.conn.execute(
                    "UPDATE supported_symbols SET is_active = FALSE WHERE symbol = ? AND exchange = ?",
                    [symbol, exchange]
                )
                
            return len(to_add), len(to_deactivate)
        except Exception as e:
            self.logger.error(f"Error updating supported symbols: {e}")
            return 0, 0


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

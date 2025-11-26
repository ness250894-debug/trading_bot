import logging
from . import config

# Configure logging
logger = logging.getLogger("Edge")

class Edge:
    def __init__(self):
        self.enabled = getattr(config, 'EDGE_ENABLED', False)
        self.window = getattr(config, 'EDGE_WINDOW_TRADES', 10)
        self.min_expectancy = getattr(config, 'EDGE_MIN_EXPECTANCY', 0.0)

    def calculate_expectancy(self, trades):
        """
        Calculates Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        Returns: float (Expectancy)
        """
        if not trades:
            return 0.0

        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [abs(t['pnl']) for t in trades if t['pnl'] <= 0]

        count_wins = len(wins)
        count_losses = len(losses)
        total_trades = len(trades)

        if total_trades == 0:
            return 0.0

        win_rate = count_wins / total_trades
        loss_rate = count_losses / total_trades

        avg_win = sum(wins) / count_wins if count_wins > 0 else 0.0
        avg_loss = sum(losses) / count_losses if count_losses > 0 else 0.0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        logger.info(f"Edge Calc: WinRate: {win_rate:.2f}, AvgWin: {avg_win:.4f}, AvgLoss: {avg_loss:.4f} => Exp: {expectancy:.4f}")
        return expectancy

    def check_edge(self, db_handler):
        """
        Checks if the current strategy expectancy is positive.
        Returns: True (Safe to trade) or False (Stop trading)
        """
        if not self.enabled:
            return True

        # Fetch last N trades
        # We need to implement get_recent_trades in db_handler or use a raw query
        # For now, let's assume db_handler has a method or we add it.
        # Since we are in the same codebase, let's look at database.py first or assume we can add it.
        # Actually, let's just use the existing get_trades and filter in python for simplicity if needed,
        # or better, add a method to DuckDBHandler.
        
        try:
            # We'll assume get_recent_trades exists or we'll add it to database.py next.
            # If not, we can use get_trades() and slice.
            if hasattr(db_handler, 'get_recent_trades'):
                trades = db_handler.get_recent_trades(self.window)
            else:
                # Fallback if method doesn't exist yet (we should add it)
                all_trades = db_handler.get_trades()
                trades = all_trades[-self.window:] if all_trades else []
            
            if len(trades) < 5:
                # Not enough data to determine edge, assume safe (or unsafe depending on preference)
                # Let's assume safe to build history
                return True

            expectancy = self.calculate_expectancy(trades)
            
            if expectancy > self.min_expectancy:
                return True
            else:
                logger.warning(f"⛔ Edge is negative ({expectancy:.4f} <= {self.min_expectancy}). Stopping trade.")
                return False

        except Exception as e:
            logger.error(f"Failed to check edge: {e}")
            return True # Fail safe: Allow trading if check fails? Or Block? 
                        # Let's Allow to avoid blocking on DB errors, but log error.

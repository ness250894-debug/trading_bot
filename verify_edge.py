import logging
from unittest.mock import MagicMock
from backend.app.core import config
from backend.app.core.edge import Edge

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestEdge")

def verify_edge_logic():
    print("--- Testing Edge Positioning Logic ---")
    
    # Mock Config
    config.EDGE_ENABLED = True
    config.EDGE_WINDOW_TRADES = 5
    config.EDGE_MIN_EXPECTANCY = 0.0
    
    edge = Edge()
    
    # Mock DB Handler
    db = MagicMock()
    
    # Case 1: Positive Edge
    print("\n1. Testing Positive Edge...")
    # 3 Wins, 2 Losses
    trades_positive = [
        {'pnl': 10}, {'pnl': 10}, {'pnl': 10}, # Wins
        {'pnl': -5}, {'pnl': -5}               # Losses
    ]
    # Win Rate: 0.6, Avg Win: 10, Avg Loss: 5
    # Exp: (0.6 * 10) - (0.4 * 5) = 6 - 2 = 4.0 (Positive)
    
    db.get_recent_trades.return_value = trades_positive
    result = edge.check_edge(db)
    print(f"   Result: {result} (Expected: True)")
    
    # Case 2: Negative Edge
    print("\n2. Testing Negative Edge...")
    # 1 Win, 4 Losses
    trades_negative = [
        {'pnl': 5},                            # Win
        {'pnl': -10}, {'pnl': -10}, {'pnl': -10}, {'pnl': -10} # Losses
    ]
    # Win Rate: 0.2, Avg Win: 5, Avg Loss: 10
    # Exp: (0.2 * 5) - (0.8 * 10) = 1 - 8 = -7.0 (Negative)
    
    db.get_recent_trades.return_value = trades_negative
    result = edge.check_edge(db)
    print(f"   Result: {result} (Expected: False)")

if __name__ == "__main__":
    verify_edge_logic()

import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(__file__))

from app.core.database import DuckDBHandler

def clear_all_users():
    print("=== Clear All Users ===")
    print("⚠️  WARNING: This will delete ALL users and related data!")
    confirm = input("Type 'DELETE ALL' to confirm: ").strip()
    
    if confirm != "DELETE ALL":
        print("❌ Cancelled.")
        return
    
    db = DuckDBHandler()
    
    try:
        # Delete all related data
        db.conn.execute("DELETE FROM subscriptions")
        db.conn.execute("DELETE FROM user_strategies")
        db.conn.execute("DELETE FROM api_keys")
        db.conn.execute("DELETE FROM trades")
        db.conn.execute("DELETE FROM backtest_results")
        db.conn.execute("DELETE FROM payments")
        db.conn.execute("DELETE FROM visual_strategies")
        db.conn.execute("DELETE FROM public_strategies")
        db.conn.execute("DELETE FROM strategy_clones")
        db.conn.execute("DELETE FROM audit_log")
        
        # Delete all users
        db.conn.execute("DELETE FROM users")
        
        print("✅ All users and related data deleted successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_all_users()

"""
Database migration script to add user_id to existing data.
Migrates single-user data to multi-tenant schema.
"""
import duckdb
import json
import os
from datetime import datetime

DB_PATH = "data/trading_bot.duckdb"
CONFIG_PATH = "backend/app/core/config.json"

def migrate_database():
    """Migrate existing database to multi-tenant schema."""
    print("Starting database migration...")
    
    if not os.path.exists(DB_PATH):
        print(f"✗ Database not found at {DB_PATH}")
        return False
    
    conn = duckdb.connect(DB_PATH)
    
    # Get the first user ID (or create a default user)
    result = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    
    if result:
        default_user_id = result[0]
        print(f"✓ Found existing user with ID: {default_user_id}")
    else:
        print("✗ No users found. Please create a user first via /api/auth/signup")
        return False
    
    # Migrate trades
    print("\nMigrating trades...")
    try:
        # Check if user_id column exists
        conn.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS user_id INTEGER")
        
        # Update NULL user_ids to default user
        result = conn.execute("""
            UPDATE trades 
            SET user_id = ? 
            WHERE user_id IS NULL
        """, [default_user_id])
        
        count = conn.execute("SELECT COUNT(*) FROM trades WHERE user_id = ?", [default_user_id]).fetchone()[0]
        print(f"✓ Migrated {count} trades to user {default_user_id}")
    except Exception as e:
        print(f"✗ Error migrating trades: {e}")
    
    # Migrate backtest results
    print("\nMigrating backtest results...")
    try:
        conn.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS user_id INTEGER")
        
        result = conn.execute("""
            UPDATE backtest_results 
            SET user_id = ? 
            WHERE user_id IS NULL
        """, [default_user_id])
        
        count = conn.execute("SELECT COUNT(*) FROM backtest_results WHERE user_id = ?", [default_user_id]).fetchone()[0]
        print(f"✓ Migrated {count} backtest results to user {default_user_id}")
    except Exception as e:
        print(f"✗ Error migrating backtest results: {e}")
    
    # Migrate config.json to database
    print("\nMigrating config.json...")
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            # Check if strategy already exists for this user
            existing = conn.execute("""
                SELECT COUNT(*) FROM strategies 
                WHERE user_id = ? AND is_active = TRUE
            """, [default_user_id]).fetchone()[0]
            
            if existing == 0:
                # Insert config as strategy
                timestamp = datetime.now()
                config_json = json.dumps(config)
                strategy_name = config.get('STRATEGY', 'default')
                
                conn.execute("""
                    INSERT INTO strategies 
                    (id, user_id, name, config_json, is_active, created_at, updated_at)
                    VALUES (nextval('seq_strategy_id'), ?, ?, ?, TRUE, ?, ?)
                """, [default_user_id, strategy_name, config_json, timestamp, timestamp])
                
                print(f"✓ Migrated config.json to strategies table")
            else:
                print(f"ℹ Strategy already exists for user {default_user_id}, skipping")
        except Exception as e:
            print(f"✗ Error migrating config: {e}")
    else:
        print(f"ℹ No config.json found at {CONFIG_PATH}")
    
    conn.close()
    print("\n✅ Migration complete!")
    return True

def verify_migration():
    """Verify migration was successful."""
    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)
    
    conn = duckdb.connect(DB_PATH)
    
    # Check trades
    result = conn.execute("""
        SELECT user_id, COUNT(*) as count 
        FROM trades 
        GROUP BY user_id
    """).fetchall()
    
    print("\nTrades by user:")
    for row in result:
        print(f"  User {row[0]}: {row[1]} trades")
    
    # Check backtest results
    result = conn.execute("""
        SELECT user_id, COUNT(*) as count 
        FROM backtest_results 
        GROUP BY user_id
    """).fetchall()
    
    print("\nBacktest results by user:")
    for row in result:
        print(f"  User {row[0]}: {row[1]} results")
    
    # Check strategies
    result = conn.execute("""
        SELECT user_id, name, is_active 
        FROM strategies
    """).fetchall()
    
    print("\nStrategies:")
    for row in result:
        active = "✓" if row[2] else " "
        print(f"  [{active}] User {row[0]}: {row[1]}")
    
    conn.close()
    print("="*60 + "\n")

if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION TO MULTI-TENANT SCHEMA")
    print("="*60 + "\n")
    
    if migrate_database():
        verify_migration()
        print("✅ Migration successful! You can now use the multi-tenant API.")
    else:
        print("❌ Migration failed. Please fix errors and try again.")

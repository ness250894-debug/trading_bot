import sys
import os
import json
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is .../backend
# We want to import app from backend.app
sys.path.append(current_dir) # Add backend folder
sys.path.append(os.path.dirname(current_dir)) # Add root folder

from app.core.database import DuckDBHandler
from app.core import config

def seed_plans():
    print("--- Seeding Subscription Plans ---")
    db = DuckDBHandler(config.DB_PATH)
    
    plans = [
        # Free Tier
        {
            "id": "free",
            "name": "Free Tier",
            "price": 0.0,
            "currency": "USD",
            "duration_days": 36500, # indefinitely
            "features": [
                "paper_trading",
                "strategy_mean_reversion",
                "max_bots_1",
                "price_alerts",
                "manual_trading_history",
                "market_data_access"
            ]
        },
        # Basic
        {
            "id": "basic_monthly",
            "name": "Basic (Monthly)",
            "price": 19.0,
            "currency": "USD",
            "duration_days": 30,
            "features": [
                "live_trading", 
                "max_bots_3", 
                "standard_strategies", 
                "sentiment_standard", 
                "realtime_data"
            ]
        },
        {
            "id": "basic_yearly",
            "name": "Basic (Yearly)",
            "price": 190.0,
            "currency": "USD",
            "duration_days": 365,
            "features": [
                "live_trading", 
                "max_bots_3", 
                "standard_strategies", 
                "sentiment_standard", 
                "realtime_data"
            ]
        },
        # Pro
        {
            "id": "pro_monthly",
            "name": "Pro (Monthly)",
            "price": 49.0,
            "currency": "USD",
            "duration_days": 30,
            "features": [
                "live_trading", 
                "max_bots_10", 
                "visual_builder", 
                "backtesting", 
                "optimization_standard", 
                "sentiment_advanced", 
                "quick_scalp"
            ]
        },
        {
            "id": "pro_yearly",
            "name": "Pro (Yearly)",
            "price": 490.0,
            "currency": "USD",
            "duration_days": 365,
            "features": [
                "live_trading", 
                "max_bots_10", 
                "visual_builder", 
                "backtesting", 
                "optimization_standard", 
                "sentiment_advanced", 
                "quick_scalp"
            ]
        },
        # Elite
        {
            "id": "elite_monthly",
            "name": "Elite (Monthly)",
            "price": 99.0,
            "currency": "USD",
            "duration_days": 30,
            "features": [
                "live_trading", 
                "max_bots_unlimited", 
                "visual_builder", 
                "backtesting", 
                "optimization_ultimate", 
                "sentiment_advanced", 
                "quick_scalp",
                "priority_support",
                "unlimited_exchanges"
            ]
        },
        {
            "id": "elite_yearly",
            "name": "Elite (Yearly)",
            "price": 990.0,
            "currency": "USD",
            "duration_days": 365,
            "features": [
                "live_trading", 
                "max_bots_unlimited", 
                "visual_builder", 
                "backtesting", 
                "optimization_ultimate", 
                "sentiment_advanced", 
                "quick_scalp",
                "priority_support",
                "unlimited_exchanges"
            ]
        }
    ]
    
    conn = db.conn
    
    # Optional: Clear existing plans if you want to start fresh (careful in prod)
    # conn.execute("DELETE FROM plans WHERE id LIKE 'basic_%' OR id LIKE 'pro_%' OR id LIKE 'elite_%'")

    for plan in plans:
        # Check if exists
        existing = conn.execute("SELECT 1 FROM plans WHERE id = ?", [plan['id']]).fetchone()
        
        now = datetime.now()
        
        if existing:
            print(f"Updating plan: {plan['name']}")
            conn.execute("""
                UPDATE plans 
                SET name = ?, price = ?, currency = ?, duration_days = ?, features = ?, updated_at = ?
                WHERE id = ?
            """, [
                plan['name'], 
                plan['price'], 
                plan['currency'], 
                plan['duration_days'], 
                json.dumps(plan['features']), 
                now, 
                plan['id']
            ])
        else:
            print(f"Creating plan: {plan['name']}")
            conn.execute("""
                INSERT INTO plans (id, name, price, currency, duration_days, features, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                plan['id'],
                plan['name'],
                plan['price'],
                plan['currency'],
                plan['duration_days'],
                json.dumps(plan['features']),
                True,
                now,
                now
            ])
            
    print("✅ Plans seeded successfully.")

if __name__ == "__main__":
    seed_plans()

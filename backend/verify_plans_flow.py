import sys
import os
import json
from datetime import datetime

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is .../backend
# We want to import 'app' which is inside 'backend'. So we need 'backend' in path?
# No, if we do 'from app...', 'app' must be a package in one of sys.path folders.
# 'app' is in 'backend'. So 'backend' folder must be in sys.path.
sys.path.append(current_dir)
# Also append root for config if needed? (Config usually in app.core.config)
sys.path.append(os.path.dirname(current_dir))

from app.core.database import DuckDBHandler

def verify_flow():
    print("--- Starting Plans Flow Verification ---")
    db = DuckDBHandler()
    
    # 1. Verify Plans Exist (Pricing Page Data)
    print("\n1. Verifying Plans (Pricing Page Data)...")
    plans = db.get_plans()
    if not plans:
        print("FAIL: No plans found!")
        return
        
    expected_plans = ['basic_monthly', 'pro_monthly', 'elite_monthly', 'basic_yearly', 'pro_yearly', 'elite_yearly']
    found_ids = [p['id'] for p in plans]
    print(f"Found Plans: {found_ids}")
    
    # Verify 'Free' plan exists
    if 'free' not in found_ids:
        print("FAIL: Free plan not found!")
    else:
        print("SUCCESS: Free plan found.")

    # 1.1 Verify Display Features (User Friendly)
    # We can't call API directly easily here without starting server, 
    # but we can check if we can simulate the formatting logic if we imported it?
    # Or just rely on code review. 
    # Let's AT LEAST check that 'free' plan in DB has correct raw features.
    free_plan = next(p for p in plans if p['id'] == 'free')
    print(f"Free Plan Features: {free_plan.get('features')}")
    if 'paper_trading' in free_plan.get('features', []):
         print("SUCCESS: Free plan has expected raw features.")
    
    # 2. Simulate User & Admin Assignment
    print("\n2. Verifying Admin Assignment & Feature Gating...")
    
    # Create temp user
    email = "test_flow_verify@example.com"
    user = db.get_user_by_email(email)
    if not user:
        user_id = db.create_user(email, "hashed_pass")
    else:
        user_id = user['id']
        
    # Helper to check features
    def check_plan_features(plan_id, expected_features, unexpected_features):
        print(f"\nAssigning Plan: {plan_id}")
        # Admin assignment
        db.update_user_subscription(user_id, plan_id, 'active')
        
        # Check Features
        features = db.get_user_features(user_id)
        # Simulate what /billing/status would return
        billing_response = {
            'plan': plan_id,
            'status': 'active',
            'features': features
        }
        print(f"  > /billing/status Response: {json.dumps(billing_response)}")
        
        all_passed = True
        for ef in expected_features:
            if ef not in features:
                print(f"  FAIL: Expected '{ef}' not found.")
                all_passed = False
        
        for uf in unexpected_features:
            if uf in features:
                print(f"  FAIL: Unexpected '{uf}' found.")
                all_passed = False
                
        if all_passed:
            print("  SUCCESS: Features match expected gates.")

    # Test FREE -> Should have Paper Trading, 1 Bot.
    check_plan_features('free', 
                        expected_features=['paper_trading', 'max_bots_1'], 
                        unexpected_features=['live_trading', 'visual_builder'])

            
    # Test BASIC -> Should have Live Trading, NO Visual Builder
    check_plan_features('basic_monthly', 
                        expected_features=['live_trading', 'max_bots_3'], 
                        unexpected_features=['visual_builder', 'max_bots_10', 'optimization_ultimate'])

    # Test PRO -> Should have Visual Builder, 10 Bots
    check_plan_features('pro_monthly', 
                        expected_features=['live_trading', 'max_bots_10', 'visual_builder', 'backtesting'], 
                        unexpected_features=['max_bots_unlimited'])

    # Test ELITE -> Should have Unlimited Bots
    check_plan_features('elite_monthly', 
                        expected_features=['live_trading', 'max_bots_unlimited', 'optimization_ultimate'], 
                        unexpected_features=[])
                        
    # Cleanup
    db.delete_user(user_id)
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_flow()

import requests
import duckdb
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:8000/api"
DB_FILE = "data/trading_bot.duckdb"



def get_token(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def register_user(email, password):
    requests.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": password})

def test_isolation():
    # Register/Login User 1
    email1 = "user1@test.com"
    pass1 = "password123"
    register_user(email1, pass1)
    token1 = get_token(email1, pass1)
    
    # Register/Login User 2
    email2 = "user2@test.com"
    pass2 = "password123"
    register_user(email2, pass2)
    token2 = get_token(email2, pass2)
    
    if not token1 or not token2:
        print("Failed to get tokens.")
        return

    # Check User 1 Trades
    headers1 = {"Authorization": f"Bearer {token1}"}
    resp1 = requests.get(f"{BASE_URL}/trades", headers=headers1)
    trades1 = resp1.json()
    print(f"User 1 Trades: {[t['symbol'] for t in trades1]}")
    
    # Verify User 1 sees ONLY User 1 trades (and maybe legacy if we decided that, but currently strict)
    # Current implementation is strict: WHERE user_id = ?
    # So User 1 should NOT see TEST/USER2 or TEST/LEGACY
    
    user1_symbols = [t['symbol'] for t in trades1]
    if 'TEST/USER1' in user1_symbols and 'TEST/USER2' not in user1_symbols:
        print("PASS: User 1 sees correct trades.")
    else:
        print("FAIL: User 1 sees incorrect trades.")

    # Check User 2 Trades
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp2 = requests.get(f"{BASE_URL}/trades", headers=headers2)
    trades2 = resp2.json()
    print(f"User 2 Trades: {[t['symbol'] for t in trades2]}")
    
    user2_symbols = [t['symbol'] for t in trades2]
    if 'TEST/USER2' in user2_symbols and 'TEST/USER1' not in user2_symbols:
        print("PASS: User 2 sees correct trades.")
    else:
        print("FAIL: User 2 sees incorrect trades.")

if __name__ == "__main__":
    # We need to ensure the DB has the columns first. 
    # The server startup creates them.
    # So we should run this AFTER server start.
    # setup_test_data() # Moved to seed_data.py
    test_isolation()

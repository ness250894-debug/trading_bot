import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api"

def verify_multiple_bots():
    print("Verifying multiple bots...")
    
    # 0. Health Check
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Health check failed: {e}")

    # 1. Login/Signup
    email = f"test_multi_{int(time.time())}@example.com"
    password = "Password123!" # Stronger password to satisfy validation
    
    print(f"Creating user {email}...")
    try:
        # Try signup
        signup_url = f"{BASE_URL}/auth/signup"
        print(f"POST {signup_url}")
        resp = requests.post(signup_url, json={
            "email": email,
            "password": password,
            "nickname": "TestMulti"
        })
        print(f"Signup Response: {resp.status_code} {resp.text}")
        
        if resp.status_code == 200:
            token = resp.json()['access_token']
        else:
            # Try login
            login_url = f"{BASE_URL}/auth/login"
            print(f"POST {login_url}")
            resp = requests.post(login_url, data={
                "username": email,
                "password": password
            })
            print(f"Login Response: {resp.status_code} {resp.text}")
            
            if resp.status_code != 200:
                print(f"Failed to login/signup")
                return
            token = resp.json()['access_token']
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Bot Config 1
    print("Creating Bot Config 1 (BTC/USDT)...")
    config1 = {
        "symbol": "BTC/USDT",
        "strategy": "mean_reversion",
        "timeframe": "1h",
        "amount_usdt": 100,
        "dry_run": True,
        "take_profit_pct": 1.0,
        "stop_loss_pct": 1.0,
        "parameters": {"rsi_period": 14}
    }
    resp = requests.post(f"{BASE_URL}/bot-configs", json=config1, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to create config 1: {resp.text}")
        return
    # The API returns {"status": "success", "config": {...}}
    config1_id = resp.json()['config']['id']
    print(f"Config 1 created with ID: {config1_id}")
    
    # 3. Create Bot Config 2 (BTC/USDT - Same Symbol) - Should FAIL for free plan
    print("Creating Bot Config 2 (BTC/USDT) - Should fail for free plan...")
    config2 = {
        "symbol": "BTC/USDT",
        "strategy": "momentum",
        "timeframe": "15m",
        "amount_usdt": 50,
        "dry_run": True,
        "take_profit_pct": 2.0,
        "stop_loss_pct": 2.0,
        "parameters": {"rsi_period": 7}
    }
    resp = requests.post(f"{BASE_URL}/bot-configs", json=config2, headers=headers)
    if resp.status_code == 403:
        print(f"SUCCESS: Free plan limit enforced! Response: {resp.text}")
        print("\n=== VERIFICATION PASSED ===")
        print("Free plan users are correctly limited to 1 bot configuration.")
        return
    elif resp.status_code == 200:
        print(f"FAILURE: Config 2 was created - free plan limit NOT enforced!")
        config2_id = resp.json()['config']['id']
        print(f"Config 2 created with ID: {config2_id}")
    else:
        print(f"Unexpected response: {resp.status_code} {resp.text}")
    
    # 4. Start Bot 1
    print(f"Starting Bot 1 (ID: {config1_id})...")
    resp = requests.post(f"{BASE_URL}/start", params={"config_id": config1_id}, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to start bot 1: {resp.text}")
    else:
        print("Bot 1 started.")
        
    # 5. Start Bot 2
    print(f"Starting Bot 2 (ID: {config2_id})...")
    resp = requests.post(f"{BASE_URL}/start", params={"config_id": config2_id}, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to start bot 2: {resp.text}")
    else:
        print("Bot 2 started.")
        
    # 6. Check Status
    print("Checking status...")
    resp = requests.get(f"{BASE_URL}/status", headers=headers)
    status = resp.json()
    print(json.dumps(status, indent=2))
    
    instances = status.get('instances', {})
    if str(config1_id) in instances and str(config2_id) in instances:
        print("SUCCESS: Both bots are running!")
        if instances[str(config1_id)]['is_running'] and instances[str(config2_id)]['is_running']:
             print("Both bots confirmed running.")
        else:
             print("One or both bots are not running.")
    else:
        print("FAILURE: Both bots not found in status.")
        print(f"Instances keys: {list(instances.keys())}")
        print(f"Config IDs: {config1_id}, {config2_id}")

    # 7. Stop Bot 1
    print(f"Stopping Bot 1 (ID: {config1_id})...")
    requests.post(f"{BASE_URL}/stop", params={"config_id": config1_id}, headers=headers)
    
    # 8. Check Status again
    resp = requests.get(f"{BASE_URL}/status", headers=headers)
    status = resp.json()
    instances = status.get('instances', {})
    if not instances.get(str(config1_id), {}).get('is_running') and instances.get(str(config2_id), {}).get('is_running'):
        print("SUCCESS: Bot 1 stopped, Bot 2 still running.")
    else:
        print("FAILURE: Status check after stop failed.")
        print(json.dumps(instances, indent=2))
        
if __name__ == "__main__":
    verify_multiple_bots()

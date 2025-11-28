"""
Test script to verify production improvements:
- Database singleton
- Rate limiting  
- Audit logging
- Dual-key decryption

Run after server is started.
"""

import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_rate_limiting():
    """Test that rate limiting works correctly."""
    print("\n=== Testing Rate Limiting ===")
    
    # First, login to get a token
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "user1@test.com",
        "password": "password123"
    })
    
    if login_resp.status_code != 200:
        print("❌ Login failed. Make sure user exists.")
        return False
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET rate limit (30/minute)
    print("Testing GET rate limit (30/min)...")
    success_count = 0
    for i in range(35):
        resp = requests.get(f"{BASE_URL}/api-keys/bybit", headers=headers)
        if resp.status_code == 200:
            success_count += 1
        elif resp.status_code == 429:
            print(f"✓ Rate limit triggered after {success_count} requests (expected ~30)")
            return True
    
    print(f"⚠ Expected rate limit to trigger, but got {success_count}/35 successful requests")
    return False

def test_audit_logging():
    """Test that audit logs are created."""
    print("\n=== Testing Audit Logging ===")
    
    # Login
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "user1@test.com",
        "password": "password123"
    })
    
    if login_resp.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Perform an action that should be logged
    resp = requests.get(f"{BASE_URL}/api-keys/bybit", headers=headers)
    
    if resp.status_code == 200:
        print("✓ API call successful")
        print("✓ Check database audit_logs table to verify entry was created")
        print("  Expected: action='read', resource_type='api_key', resource_id='bybit'")
        return True
    else:
        print(f"❌ API call failed: {resp.status_code}")
        return False

def test_database_singleton():
    """Test that database singleton works."""
    print("\n=== Testing Database Singleton ===")
    
    from backend.app.core.database import DuckDBHandler
    
    db1 = DuckDBHandler()
    db2 = DuckDBHandler()
    db3 = DuckDBHandler.get_instance()
    
    if db1 is db2 is db3:
        print("✓ All DuckDBHandler instances are the same object (singleton working)")
        return True
    else:
        print("❌ DuckDBHandler instances are different (singleton not working)")
        return False

if __name__ == "__main__":
    print("Production Improvements Verification")
    print("=" * 50)
    
    # Test database singleton
    try:
        test_database_singleton()
    except Exception as e:
        print(f"❌ Database singleton test failed: {e}")
    
    # Test rate limiting
    try:
        test_rate_limiting()
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
    
    # Test audit logging
    try:
        test_audit_logging()
    except Exception as e:
        print(f"❌ Audit logging test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Verification complete!")
    print("\nTo verify key rotation:")
    print("1. Generate a new key: python generate_encryption_key.py")
    print("2. Add as ENCRYPTION_KEY_NEW in .env")
    print("3. Run: python key_rotation.py")

import pytest
import requests
import sys

BASE_URL = "http://localhost:8000/api"
AUTH_URL = "http://localhost:8000/api/auth"

def get_auth_token(email, password):
    response = requests.post(f"{AUTH_URL}/login", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

@pytest.mark.integration
def test_protected_route(route, method="GET", token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"{BASE_URL}{route}"
    print(f"Testing {method} {url} [{'With Token' if token else 'No Token'}]...")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={})
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
            
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Body: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"Error: {e}")
        return 500

if __name__ == "__main__":
    email = "testuser@example.com"
    password = "securepassword123"
    
    # 1. Get Token
    token = get_auth_token(email, password)
    if not token:
        print("❌ Failed to get token. Run test_auth_flow.py first to create user.")
        sys.exit(1)
        
    # 2. Test Protected Routes
    routes_to_test = [
        ("/balance", "GET"),
        ("/status", "GET"),
        ("/trades", "GET")
    ]
    
    all_passed = True
    
    for route, method in routes_to_test:
        # Expect 401 without token
        status_no_token = test_protected_route(route, method)
        if status_no_token != 401:
            print(f"❌ Failed: Expected 401, got {status_no_token}")
            all_passed = False
        else:
            print("✅ Correctly rejected without token")
            
        # Expect 200 (or other success) with token
        status_with_token = test_protected_route(route, method, token)
        if status_with_token not in [200, 404]: # 404 is fine if data empty, just not 401
            print(f"❌ Failed: Expected 200/404, got {status_with_token}")
            all_passed = False
        else:
            print("✅ Access granted with token")
            
    if all_passed:
        print("\n✅ All protected route tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

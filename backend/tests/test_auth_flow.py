import requests
import sys

BASE_URL = "http://localhost:8000/api/auth"

def test_signup(email, password):
    print(f"Testing Signup for {email}...")
    response = requests.post(f"{BASE_URL}/signup", json={"email": email, "password": password})
    if response.status_code == 200:
        print("✅ Signup Successful")
        print(response.json())
        return True
    else:
        print(f"❌ Signup Failed: {response.status_code} - {response.text}")
        return False

def test_login(email, password):
    print(f"Testing Login for {email}...")
    # OAuth2PasswordRequestForm expects form data, not JSON
    response = requests.post(f"{BASE_URL}/login", data={"username": email, "password": password})
    if response.status_code == 200:
        print("✅ Login Successful")
        print(response.json())
        return True
    else:
        print(f"❌ Login Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    email = "testuser@example.com"
    password = "securepassword123"
    
    # Try login first (might fail if user doesn't exist)
    if not test_login(email, password):
        # Try signup
        if test_signup(email, password):
            # Try login again
            test_login(email, password)

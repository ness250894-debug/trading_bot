import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(__file__))

from app.core.database import DuckDBHandler
from app.core.auth import get_password_hash

def make_admin():
    print("=== Make User Admin ===")
    email = input("Enter user email: ").strip()
    
    if not email:
        print("Email cannot be empty.")
        return

    db = DuckDBHandler()
    user = db.get_user_by_email(email)
    
    if not user:
        print(f"User '{email}' not found.")
        create = input("Do you want to create this user? (y/n): ").lower()
        if create == 'y':
            password = input("Enter password for new user: ").strip()
            if not password:
                print("Password cannot be empty.")
                return
            
            hashed_pw = get_password_hash(password)
            success = db.create_user(email, hashed_pw)
            if success:
                print(f"User '{email}' created.")
                user = db.get_user_by_email(email)
            else:
                print("Failed to create user.")
                return
        else:
            return
        
    if user.get('is_admin'):
        print(f"User '{email}' is already an admin.")
        return
        
    success = db.set_admin_status(user['id'], True)
    
    if success:
        print(f"✅ Success! User '{email}' is now an admin.")
    else:
        print("❌ Failed to update user status.")

if __name__ == "__main__":
    make_admin()

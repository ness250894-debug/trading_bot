import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(__file__))

from app.core.database import DuckDBHandler

def make_admin():
    print("=== Make User Admin ===")
    email = input("Enter user email: ").strip()
    
    if not email:
        print("Email cannot be empty.")
        return

    db = DuckDBHandler()
    user = db.get_user_by_email(email)
    
    if not user:
        print(f"User with email '{email}' not found.")
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

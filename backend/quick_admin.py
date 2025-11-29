"""Quick script to make yourself admin"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import DuckDBHandler

db = DuckDBHandler()

# Get all users
users = db.get_all_users()
print("\n=== Current Users ===")
for user in users:
    admin_status = "✅ ADMIN" if user.get('is_admin') else "👤 User"
    print(f"ID: {user['id']} | {user['email']} | {admin_status}")

if users:
    print("\n" + "="*50)
    user_id = input("Enter the ID of the user to make admin (or press Enter to cancel): ").strip()
    
    if user_id:
        try:
            user_id = int(user_id)
            success = db.set_admin_status(user_id, True)
            if success:
                print(f"\n✅ User ID {user_id} is now an ADMIN!")
                print("Refresh your admin panel page to see all users.")
            else:
                print("\n❌ Failed to update admin status")
        except ValueError:
            print("Invalid user ID")
else:
    print("\nNo users found. Please register an account first!")

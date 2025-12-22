import os
import shutil

def cleanup_shadow_dbs():
    root = os.getcwd()
    shadow = os.path.join(root, "backend", "data", "trading_bot.duckdb")
    
    if os.path.exists(shadow):
        print(f"Found shadow DB at {shadow}")
        try:
            os.remove(shadow)
            print("Successfully deleted shadow DB.")
        except PermissionError:
            print("Cannot delete shadow DB - it is currently in use (LOCKED).")
            print("This implies the running application might be using it, OR a zombie process.")
        except Exception as e:
            print(f"Error deleting shadow DB: {e}")
    else:
        print("No shadow DB found at backend/data/")

if __name__ == "__main__":
    cleanup_shadow_dbs()

import os
import duckdb
import datetime

def check_db(path):
    print(f"--- Checking {path} ---")
    if not os.path.exists(path):
        print("File not found.")
        return
        
    stats = os.stat(path)
    print(f"Size: {stats.st_size / 1024 / 1024:.2f} MB")
    print(f"Modified: {datetime.datetime.fromtimestamp(stats.st_mtime)}")
    
    try:
        conn = duckdb.connect(path, read_only=True)
        count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        print(f"User Count: {count}")
        
        # Show recent users
        users = conn.execute("SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 3").fetchall()
        for u in users:
            print(f"  User: {u[0]} at {u[1]}")
            
    except Exception as e:
        print(f"Error reading DB: {e}")

def main():
    root = os.getcwd()
    output = []
    output.append(f"Root: {root}")
    
    candidates = [
        "data/trading_bot.duckdb",
        "backend/data/trading_bot.duckdb",
        "backend/tests/data/trading_bot.duckdb"
    ]
    
    for c in candidates:
        full_path = os.path.join(root, c)
        output.append(f"\n--- Checking {c} ---")
        if not os.path.exists(full_path):
            output.append("File not found.")
            continue
            
        stats = os.stat(full_path)
        output.append(f"Size: {stats.st_size / 1024 / 1024:.2f} MB")
        output.append(f"Modified: {datetime.datetime.fromtimestamp(stats.st_mtime)}")
        
        try:
            conn = duckdb.connect(full_path, read_only=True)
            count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
            output.append(f"User Count: {count}")
            
            users = conn.execute("SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 3").fetchall()
            for u in users:
                output.append(f"  User: {u[0]} at {u[1]}")
            conn.close()
                
        except Exception as e:
            output.append(f"Error reading DB: {e}")
            
    with open("db_report.txt", "w") as f:
        f.write("\n".join(output))
    print("Report written to db_report.txt")

if __name__ == "__main__":
    main()

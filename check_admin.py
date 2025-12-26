import sqlite3
import os

storage_dir = os.environ.get("STORAGE_PATH", ".")
db_path = "adw.db" # Local check

print(f"Checking DB: {db_path}")

try:
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        print("\nUSERS TABLE:")
        print("ID | Username | Role")
        print("-" * 30)
        for u in users:
            # u structure: id, username, pass_hash, role, created_at
            print(f"{u[0]} | {u[1]} | {u[3]}")
            
except Exception as e:
    print(f"Error: {e}")

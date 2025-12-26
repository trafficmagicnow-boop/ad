"""Test Admin User Management API"""
import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

def req(endpoint, data=None, token=None, method=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Cookie"] = f"session={token}"
    
    if data:
        encoded_data = json.dumps(data).encode()
    else:
        encoded_data = None
        
    r = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body), resp.headers.get('Set-Cookie', '')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()), ""
    except Exception as e:
        return 0, str(e), ""

print("="*50)
print("TESTING ADMIN USER MANAGEMENT")
print("="*50)

# 1. Login as Admin
print("\n[1] Login as Admin...")
status, body, cookie = req("/api/login", {"username": "admin", "password": "admin123"})
if status != 200:
    print(f"[FAIL] Admin login failed: {body}")
    exit(1)
admin_token = cookie.split('session=')[1].split(';')[0]
print(f"[OK] Admin logged in. Token: {admin_token[:10]}...")

# 2. Create New User
print("\n[2] Create 'testuser'...")
status, body, _ = req("/api/admin/users/create", 
                     {"username": "testuser", "password": "pass123", "role": "user"},
                     token=admin_token)
if status == 200 and body.get("status") == "ok":
    print(f"[OK] User created")
else:
    print(f"[FAIL] Create user failed: {body}")
    exit(1)

# 3. List Users
print("\n[3] List Users...")
status, body, _ = req("/api/admin/users", token=admin_token)
users = body.get("users", [])
found = False
test_user_id = None
for u in users:
    if u["username"] == "testuser":
        found = True
        test_user_id = u["id"]
        print(f"[OK] Found created user: ID={u['id']}, Role={u['role']}")
        break
if not found:
    print("[FAIL] 'testuser' not found in list")
    exit(1)

# 4. Login as New User
print("\n[4] Login as 'testuser'...")
status, body, cookie = req("/api/login", {"username": "testuser", "password": "pass123"})
if status != 200:
    print(f"[FAIL] testuser login failed: {body}")
    exit(1)
user_token = cookie.split('session=')[1].split(';')[0]
print(f"[OK] testuser logged in")

# 5. Access Check (User trying to list users)
print("\n[5] Access Check (User -> /api/admin/users)...")
status, body, _ = req("/api/admin/users", token=user_token)
if status == 403:
    print(f"[OK] Access denied correctly (403): {body.get('message')}")
else:
    print(f"[FAIL] User accessing admin endpoint returned {status}: {body}")
    exit(1)

# 6. Delete User
print("\n[6] Delete 'testuser' (as Admin)...")
status, body, _ = req("/api/admin/users/delete", {"user_id": test_user_id}, token=admin_token)
if status == 200 and body.get("status") == "ok":
    print(f"[OK] User deleted")
else:
    print(f"[FAIL] Delete failed: {body}")
    exit(1)

# 7. Verify Deletion
print("\n[7] Verify deletion...")
status, body, _ = req("/api/admin/users", token=admin_token)
users = body.get("users", [])
found = False
for u in users:
    if u["username"] == "testuser":
        found = True
if not found:
    print("[OK] 'testuser' is gone")
else:
    print("[FAIL] 'testuser' still in list")
    exit(1)

print("\n" + "="*50)
print("ALL TESTS PASSED ✅")
print("="*50)

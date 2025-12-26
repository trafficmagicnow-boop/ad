"""Simple auth test script"""
import urllib.request
import json

# Test 1: Login
print("="*50)
print("TEST 1: Login with admin/admin123")
print("="*50)

login_data = {"username": "admin", "password": "admin123"}
req = urllib.request.Request(
    "http://localhost:8000/api/login",
    data=json.dumps(login_data).encode(),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        cookie = resp.headers.get('Set-Cookie', '')
        body = resp.read().decode()
        data = json.loads(body)
        
        print(f"[OK] Status: {resp.status}")
        print(f"[OK] Response: {json.dumps(data, indent=2)}")
        print(f"[OK] Cookie set: {bool(cookie)}")
        
        if 'session=' in cookie:
            session_token = cookie.split('session=')[1].split(';')[0]
            print(f"[OK] Session token: {session_token[:20]}...")
            
            # Test 2: Check /api/me with session
            print("\n" + "="*50)
            print("TEST 2: Check current user with session")
            print("="*50)
            
            me_req = urllib.request.Request(
                "http://localhost:8000/api/me",
                headers={"Cookie": f"session={session_token}"}
            )
            
            with urllib.request.urlopen(me_req) as me_resp:
                me_data = json.loads(me_resp.read().decode())
                print(f"[OK] User data: {json.dumps(me_data, indent=2)}")
                
            # Test 3: Logout
            print("\n" + "="*50)
            print("TEST 3: Logout")
            print("="*50)
            
            logout_req = urllib.request.Request(
                "http://localhost:8000/api/logout",
                method="POST",
                headers={"Cookie": f"session={session_token}"}
            )
            
            with urllib.request.urlopen(logout_req) as logout_resp:
                logout_data = json.loads(logout_resp.read().decode())
                print(f"[OK] Logout: {json.dumps(logout_data, indent=2)}")
            
            print("\n" + "="*50)
            print("[RESULT] ALL TESTS PASSED!")
            print("="*50)
        else:
            print("[FAIL] No session cookie in response")
            
except Exception as e:
    print(f"[FAIL] Error: {e}")

import subprocess
import time
import urllib.request
import json
import sys

def test_system():
    print("--- STARTING END-TO-END TEST (No Requests Lib) ---")
    
    # 1. Start Server
    print("[1] Starting Dashboard Server...")
    p = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2) 
    
    try:
        # 2. Check Pulse
        print("[2] Checking Server Health...")
        try:
            with urllib.request.urlopen("http://localhost:8000") as r:
                print(f"    Server Status: {r.getcode()} (Expected 200)")
        except Exception as e:
            print(f"    Server FAILED: {e}")
            return

        # 3. Simulate "Update Lists"
        print("[3] Testing Adw API Connection (Refresh Lists)...")
        try:
            req = urllib.request.Request("http://localhost:8000/api/refresh", method="POST")
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read().decode())
                print(f"    Response: {data}")
                if data.get("counts", {}).get("offers") > 0:
                    print("    [PASS] Offers fetched from API!")
                else:
                    print("    [WARN] No offers fetched (API returned 0 items).")
        except Exception as e:
            print(f"    [FAIL] Refresh call failed: {e}")

        # 4. Create Link Test
        print("\n[4] Creating Test Link (Offer: 247_nurse)...")
        payload = json.dumps({
            "offer": "247_nurse",
            "buyer": "TesterAuto",
            "keywords": "test_auto",
            "article": ""
        }).encode()
        
        try:
            req = urllib.request.Request("http://localhost:8000/api/create_link", data=payload, method="POST", headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as r:
                res = json.loads(r.read().decode())
                
                if res.get("status") == "ok":
                    url = res.get("url")
                    print(f"    [PASS] Link Created Successfully!")
                    print(f"    Generated URL: {url}")
                else:
                    print(f"    [FAIL] Link Creation Failed.")
                    print(f"    Error: {res}")
        except Exception as e:
            print(f"    [FAIL] Create call failed: {e}")

    finally:
        print("[5] Stopping Server...")
        p.terminate()

if __name__ == "__main__":
    test_system()

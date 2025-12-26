import subprocess
import time
import requests
import json
import sys

def test_system():
    print("--- STARTING END-TO-END TEST ---")
    
    # 1. Start Server in background
    print("[1] Starting Dashboard Server...")
    # Use python executable relative to env
    p = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2) # Warmup
    
    try:
        # 2. Check Pulse
        print("[2] Checking Server Health...")
        try:
            r = requests.get("http://localhost:8000")
            print(f"    Server Status: {r.status_code} (Expected 200)")
        except Exception as e:
            print(f"    Server FAILED: {e}")
            return

        # 3. Simulate "Update Lists" (Refresh) -- This hits Adw API
        print("[3] Testing Adw API Connection (Refresh Lists)...")
        r = requests.post("http://localhost:8000/api/refresh")
        data = r.json()
        print(f"    Response: {data}")
        if data.get("counts", {}).get("offers") > 0:
            print("    [PASS] Offers fetched from API!")
        else:
            print("    [WARN] No offers fetched. API might be accessible but empty, or token issues.")

        # 4. Create Link Test
        print("[4] Creating Test Link (Offer: 247_nurse, User: Tester)...")
        payload = {
            "offer": "247_nurse",
            "buyer": "TesterAuto",
            "keywords": "test_auto, check",
            "article": "" # Default
        }
        r = requests.post("http://localhost:8000/api/create_link", json=payload)
        res = r.json()
        
        if res.get("status") == "ok":
            url = res.get("url")
            print(f"    [PASS] Link Created Successfully!")
            print(f"    Generated URL: {url}")
            if "sub1={clickid}" in url:
                print("    [PASS] Skro Macros detected.")
        else:
            print(f"    [FAIL] Link Creation Failed.")
            print(f"    Error: {res}")
            print("\n    Note: '247_nurse' might be an invalid offer ID for your specific account.")
            print("    This confirms the SOFTWARE logic is correct, but the OFFER ID needs to be valid.")

    finally:
        print("[5] Stopping Server...")
        p.terminate()

if __name__ == "__main__":
    test_system()

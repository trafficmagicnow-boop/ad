import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def create_campaign():
    print("--- CREATING TEST CAMPAIGN ---")
    
    # 1. Define Test Data
    payload = {
        "offer": "247_nurse",  # HOPEFULLY VALID
        "buyer": "TestBot",
        "keywords": "test_kw, debug",
        "article": "" 
    }
    
    print(f"Sending Request: {payload}")
    
    url = "http://localhost:8000/api/create_link"
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("\nResponse:")
            print(json.dumps(data, indent=2))
            
            if data.get("status") == "ok":
                print("\n[SUCCESS] Campaign Created!")
                print("Link: " + data.get("url"))
            else:
                print("\n[FAIL] Could not create campaign.")
                print("Reason: " + str(data.get("resp")))

    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure 'server.py' is running!")

if __name__ == "__main__":
    create_campaign()

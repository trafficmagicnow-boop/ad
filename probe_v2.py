import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import sys

# Disable SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ADW_API_TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
ADW_BASE_URL = "https://api.adw.net"

def check(endpoint, method="GET", data=None):
    url = f"{ADW_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {ADW_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if data:
            req.data = json.dumps(data).encode('utf-8')

        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            content = resp.read().decode('utf-8')
            print(f"[SUCCESS] {method} {url} -> {resp.getcode()}")
            print(f"   Response: {content[:300]}...")
            return True
    except urllib.error.HTTPError as e:
        print(f"[FAIL] {method} {url} -> {e.code}")
    except Exception as e:
        print(f"[ERR] {method} {url} -> {e}")
    return False

def main():
    print("--- Probing for Offers/Landings ---")
    
    # 1. Try documented endpoints for list? 
    # Use 'POST' for /panel/links because user said "List Links API" is POST /panel/links
    # Maybe offers is similar?
    
    candidates = [
        "/panel/offers",
        "/panel/offer/list",
        "/panel/dictionary/offers", # Common in affiliate APIs
        "/panel/landings",
        "/panel/sites"
    ]
    
    for ep in candidates:
        # Try GET
        check(ep, "GET")
        # Try POST (common in this API)
        check(ep, "POST", data={})

    # The user manual mentioned "offer (string) [You can specify your values or use our list.]"
    # This implies there IS a list. 
    # If probe fails, we'll implement a 'Manual Input' or 'Config File' for offers in the dashboard.

if __name__ == "__main__":
    main()

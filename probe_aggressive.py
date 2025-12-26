import urllib.request
import urllib.error
import urllib.parse
import json
import ssl
import sys

TOKENS = ["5a4fb29a30fb14b3c7bbea8333056f86"]
BASE_URL = "https://api.adw.net"

# Context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def request(endpoint, method="GET", params=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKENS[0]}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if params:
            req.data = json.dumps(params).encode('utf-8')
        
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            code = resp.getcode()
            body = resp.read().decode('utf-8')
            return code, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def main():
    print("--- Aggressive Probe for Adw Offers/Articles ---")
    
    # 1. Dictionary / List Endpoints
    # Many panels use /dictionary/ or /list/
    
    potential_endpoints = [
        # Offers
        "/panel/offers",
        "/panel/offer/list",
        "/panel/list/offers",
        "/panel/offers_list",
        "/panel/campaigns", # Sometimes offers are called campaigns
        "/panel/catalog",
        
        # Metadata
        "/panel/dictionaries",
        "/panel/meta",
        "/panel/options",
        
        # Articles / Landings -> 'site_key'
        "/panel/sites",
        "/panel/landings",
        "/panel/prelandings",
        "/panel/articles",
        "/panel/promo",
        "/panel/creatives"
    ]

    for ep in potential_endpoints:
        # Try GET
        print(f" Checking GET {ep} ...", end=" ")
        c, b = request(ep, "GET")
        if c == 200:
            print(f"FOUND! (Size: {len(b)})")
            print(f"Sample: {b[:200]}")
        else:
            print(f"{c}")

        # Try POST (api.adw.net seems to like POST for everything)
        print(f" Checking POST {ep} ...", end=" ")
        c, b = request(ep, "POST", params={})
        if c == 200:
            print(f"FOUND! (Size: {len(b)})")
            print(f"Sample: {b[:200]}")
        else:
            print(f"{c}")

    # 2. Extract from Link Create Error?
    # Sometimes if you send invalid offer, it lists valid ones.
    print("\n Checking Create Link Error hint...")
    c, b = request("/panel/link_create", "POST", {
        "name": "test",
        "offer": "INVALID_OFFER_XYZ",
        "keywords": ["test"]
    })
    print(f"Response to invalid offer: {b[:300]}")

if __name__ == "__main__":
    main()

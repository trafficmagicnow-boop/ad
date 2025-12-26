import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
DOMAINS = ["https://api.adw.net", "https://api.ads.com"]
ENDPOINTS = [
    "/panel/offers",
    "/panel/offer/list",
    "/panel/list_offers", 
    "/panel/all_offers",
    "/panel/campaigns",
    "/panel/sites",
    "/miniapps/api/offer/list" # Sometimes hidden here
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(domain, ep, data=None):
    url = f"{domain}{ep}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        if data is not None:
            r = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
        else:
            r = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(r, context=ctx, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}

print("--- STARTING DEEP PROBE ---")

# 1. Try GET and POST on both domains
for d in DOMAINS:
    print(f"\nChecking Domain: {d}")
    for ep in ENDPOINTS:
        # Try GET
        c, res = req(d, ep)
        if c == 200 and res.get("status") == "ok":
            data = res.get("data")
            if data:
                count = len(data.get("list", []) or data if isinstance(data, list) else [])
                print(f"  [GET]  {ep}: FOUND {count} items!")
                print(f"         Preview: {str(data)[:100]}")
            else:
                print(f"  [GET]  {ep}: OK but empty data")
        
        # Try POST with common params
        c, res = req(d, ep, {"page": 1, "limit": 100})
        if c == 200 and res.get("status") == "ok":
            data = res.get("data")
            if data:
                count = len(data.get("list", []) or data if isinstance(data, list) else [])
                print(f"  [POST] {ep}: FOUND {count} items!")
                print(f"         Preview: {str(data)[:100]}")
            else:
                print(f"  [POST] {ep}: OK but empty data")

print("\n--- PROBE FINISHED ---")

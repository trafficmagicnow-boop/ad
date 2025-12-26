import urllib.request
import urllib.error
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"

# User's examples showed mixed domains.
# Stats/Create -> api.adw.net
# List Links -> api.ads.com
# Maybe List Offers is also on api.ads.com?

URLS = [
    "https://api.ads.com/panel/offers",
    "https://api.ads.com/panel/list/offers",
    "https://api.adw.net/panel/offers"
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def debug():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    for url in URLS:
        print(f"\n--- Checking {url} ---")
        
        # Try POST (standard for this API)
        try:
            # Empty payload
            req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
            with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                print(f"  [POST] Status: {r.getcode()}")
                print(f"  Body: {r.read().decode()[:300]}")
        except urllib.error.HTTPError as e:
            print(f"  [POST] Error: {e.code}")
        except Exception as e:
            print(f"  [POST] Exception: {e}")

        # Try GET
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                print(f"  [GET] Status: {r.getcode()}")
                print(f"  Body: {r.read().decode()[:300]}")
        except urllib.error.HTTPError as e:
            print(f"  [GET] Error: {e.code}")
        except Exception as e:
            print(f"  [GET] Exception: {e}")

if __name__ == "__main__":
    debug()

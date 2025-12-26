import urllib.request
import urllib.error
import json
import ssl

ADW_API_TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
ADW_BASE_URL = "https://api.adw.net"

def probe_adw_lists():
    headers = {
        "Authorization": f"Bearer {ADW_API_TOKEN}",
        "Content-Type": "application/json"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("--- Probing Adw API for Lists ---")
    
    # Likely endpoints for lists
    endpoints = [
        "/panel/offers",
        "/panel/offer_list",
        "/panel/list_offers",
        "/panel/campaigns",
        "/panel/landings",
        "/panel/sites",
        "/panel/articles",
        "/panel/promo"
    ]
    
    for ep in endpoints:
        url = f"{ADW_BASE_URL}{ep}"
        try:
            print(f"Checking {url} ...", end=" ")
            # Try GET
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                print(f"Status: {response.getcode()}")
                if response.getcode() == 200:
                    data = response.read().decode('utf-8')
                    print(f"    SUCCESS! Data start: {data[:200]}")
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}")
            # If 405, maybe it needs POST?
            if e.code == 405:
                # Try POST with empty body
                try:
                    req = urllib.request.Request(url, headers=headers, method='POST')
                    with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                         print(f"    (POST) Status: {response.getcode()}")
                         data = response.read().decode('utf-8')
                         print(f"    SUCCESS (POST)! Data start: {data[:200]}")
                except Exception as ex:
                    print(f"    (POST Failed) {ex}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    probe_adw_lists()

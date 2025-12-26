"""
Проверка всех возможных параметров для link_create
и других эндпоинтов API
"""
import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"
URL_INFO = "https://api.ads.com"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_req(domain, endpoint, data=None):
    url = f"{domain}{endpoint}"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read().decode()
            if "{" in raw:
                raw = raw[raw.find("{"):]
            result = json.loads(raw)
            return result
    except Exception as e:
        print(f"[ERROR] {endpoint}: {e}")
        return None

print("="*70)
print("COMPREHENSIVE ADW API ENDPOINT CHECK")
print("="*70)

# Test various endpoints
endpoints_to_test = [
    (URL_INFO, "/panel/sources", None, "Traffic Sources"),
    (URL_INFO, "/panel/countries", None, "Countries"),
    (URL_INFO, "/panel/devices", None, "Devices"),
    (URL_INFO, "/panel/languages", None, "Languages"),
    (URL_INFO, "/panel/browsers", None, "Browsers"),
    (URL_ACTION, "/panel/offer/list", {"limit": 10}, "Offer List with limit"),
]

for domain, endpoint, payload, description in endpoints_to_test:
    print(f"\n[TEST] {description} - {endpoint}")
    resp = api_req(domain, endpoint, payload)
    if resp:
        status = resp.get("status")
        print(f"  Status: {status}")
        if status == "ok":
            data = resp.get("data", {})
            if isinstance(data, dict):
                keys = list(data.keys())
                print(f"  Data keys: {keys}")
                
                # If it's a list, show count
                list_data = data.get("list", [])
                if list_data:
                    print(f"  List items: {len(list_data)}")
                    if list_data and len(list_data) > 0:
                        first_item = list_data[0]
                        print(f"  First item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            elif isinstance(data, list):
                print(f"  Data is list with {len(data)} items")
        else:
            print(f"  Message: {resp.get('message', 'No message')}")
    else:
        print(f"  [FAIL] No response")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("\nCurrently implementing:")
print("  ✅ /panel/link_create - Link creation")
print("  ✅ /panel/stats - Statistics")
print("  ✅ /panel/links - Link history")
print("  ✅ /panel/offer/list - Offers")
print("  ✅ /panel/sites - Sites/Articles")
print("\nPotentially useful (check above):")
print("  ? /panel/sources - Traffic sources")
print("  ? /panel/countries - Geo targeting")
print("  ? /panel/devices - Device targeting")
print("  ? /panel/languages - Language filters")
print("="*70)

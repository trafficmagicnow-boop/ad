"""
Adw API Endpoints Discovery Script
Проверяет все доступные фильтры и эндпоинты из /panel/offer/list
"""
import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_req(endpoint):
    url = f"{URL_ACTION}{endpoint}"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read().decode()
            if "{" in raw:
                raw = raw[raw.find("{"):]
            return json.loads(raw)
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

print("="*70)
print("DISCOVERING ADW API FILTERS AND ENDPOINTS")
print("="*70)

# Check /panel/offer/list for all available filters
print("\n[1] Checking /panel/offer/list filters...")
resp = api_req("/panel/offer/list")
if resp and resp.get("status") == "ok":
    filters = resp.get("data", {}).get("list", [])
    print(f"\n[OK] Found {len(filters)} filter types:")
    
    for f in filters:
        name = f.get("name", "unknown")
        values = f.get("values", [])
        print(f"\n  - Filter: {name}")
        print(f"    Type: {f.get('type', 'unknown')}")
        print(f"    Values: {len(values)} items")
        
        if len(values) <= 10:
            for v in values[:10]:
                print(f"      * {v.get('key')} = {v.get('value')}")
        else:
            print(f"      * {values[0].get('key')} = {values[0].get('value')}")
            print(f"      * ... ({len(values)-2} more)")
            print(f"      * {values[-1].get('key')} = {values[-1].get('value')}")

print("\n" + "="*70)
print("CURRENTLY USING:")
print("  - offer (offers list)")
print("  - pixel_event (pixel events)")
print("\nNOT YET USING:")
print("  - Check the output above for other available filters!")
print("="*70)

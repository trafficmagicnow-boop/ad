import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"
URL_INFO = "https://api.ads.com"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(url, ep):
    try:
        req = urllib.request.Request(f"{url}{ep}", headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("Checking Adw API offers...")
r1 = req(URL_INFO, "/panel/offers")
print(f"/panel/offers: {r1.get('status')} (Data len: {len(r1.get('data', []) or [])})")

r2 = req(URL_INFO, "/panel/list")
print(f"/panel/list: {r2.get('status')}")

# Check what we found
if r1.get("status") == "ok" and r1.get("data"):
    print("YES! Adw API returns offers.")
else:
    print("NO. Adw API did not return offers on known endpoints.")

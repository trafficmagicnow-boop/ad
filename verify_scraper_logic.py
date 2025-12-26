import urllib.request
import json
import ssl
import os

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_req(domain, endpoint, data=None):
    url = f"{domain}{endpoint}"
    try:
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"API Error ({endpoint}): {e}")
        return None

print("Testing scraper logic...")
r = api_req(URL_ACTION, "/panel/offer/list")

found = []
if r and r.get("status") == "ok":
    try:
        filters = r.get("data", {}).get("list", [])
        print(f"Filters found: {[f.get('name') for f in filters]}")
        
        offers_filter = next((f for f in filters if f.get("name") == "offer"), None)
        
        if offers_filter:
            print("Found 'offer' filter!")
            if "values" in offers_filter:
                print(f"Values count: {len(offers_filter['values'])}")
                for item in offers_filter["values"][:5]: # Show first 5
                    print(f" - {item}")
                    found.append({"id": item["key"], "name": item["value"]})
            else:
                print("'values' key missing in offer filter")
        else:
            print("'offer' filter NOT found")
            
    except Exception as e:
        print(f"Parse error: {e}")
else:
    print("API request failed or status != ok")

print(f"Total offers found: {len(found)}")

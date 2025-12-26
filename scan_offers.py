import urllib.request
import urllib.error
import json
import ssl

# User's token
TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"

# Domains to check as per first prompt
DOMAINS = [
    "https://api.adw.net",
    "https://api.ads.com" 
]

# Endpoints that might return offers
ENDPOINTS = [
    "/panel/offers",
    "/panel/offer_list",
    "/panel/list_offers",
    "/panel/offers/list",
    "/panel/all_offers",
    "/panel/marketplace",
    "/panel/catalog",
    "/panel/campaigns",
    # Sometimes it's root level
    "/offers",
    "/api/v1/offers"
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def scan():
    print("--- SCANNING FOR OFFERS LIST ---")
    
    for domain in DOMAINS:
        print(f"\nChecking Domain: {domain}")
        for ep in ENDPOINTS:
            url = f"{domain}{ep}"
            headers = {
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 1. Try GET
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=3) as r:
                    body = r.read().decode()
                    if "list" in body or "offer" in body or "data" in body:
                        print(f"  [GET] {ep} -> {r.getcode()} | CONTENT MATCH?")
                        print(f"    Sample: {body[:150]}...")
                        # If it looks like JSON list, we found it
                        try:
                            j = json.loads(body)
                            if "data" in j or isinstance(j, list):
                                print("    !!! POTENTIAL MATCH !!!")
                        except: pass
            except urllib.error.HTTPError as e:
                # print(f"  [GET] {ep} -> {e.code}")
                pass
            except: pass

            # 2. Try POST (often required for Panels)
            try:
                # With empty payload
                req = urllib.request.Request(url, headers=headers, method="POST")
                req.data = json.dumps({}).encode()
                with urllib.request.urlopen(req, context=ctx, timeout=3) as r:
                    body = r.read().decode()
                    if "list" in body or "offer" in body:
                        print(f"  [POST] {ep} -> {r.getcode()} | CONTENT MATCH?")
                        print(f"    Sample: {body[:150]}...")
                        try:
                            j = json.loads(body)
                            if "data" in j:
                                print("    !!! POTENTIAL MATCH !!!")
                        except: pass
            except urllib.error.HTTPError as e:
                # print(f"  [POST] {ep} -> {e.code}")
                pass
            except: pass

            # 3. Try POST with pagination params (common in this API)
            try:
                req = urllib.request.Request(url, headers=headers, method="POST")
                req.data = json.dumps({"page": 1, "limit": 10}).encode()
                with urllib.request.urlopen(req, context=ctx, timeout=3) as r:
                    body = r.read().decode()
                    if "list" in body:
                        print(f"  [POST+Params] {ep} -> {r.getcode()} MATCH?")
                        print(f"    Sample: {body[:150]}")
            except: pass

if __name__ == "__main__":
    scan()

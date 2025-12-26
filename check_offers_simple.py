import urllib.request
import urllib.error
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL = "https://api.adw.net/panel/offers"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def check():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"Checking {URL} ...")

    # 1. Try POST with pagination (Most likely for this specific panel software)
    try:
        data = json.dumps({"page": 1, "limit": 10, "status": "active"}).encode()
        req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            code = r.getcode()
            body = r.read().decode()
            print(f"[POST] Status: {code}")
            print(f"Body Start: {body[:300]}")
            
            # Check content
            if "list" in body and code == 200:
                print("\n>>> RESULT: SUCCESS (List Found via POST)")
                return
    except urllib.error.HTTPError as e:
        print(f"[POST] Failed: {e.code} - {e.read().decode()[:100]}")
    except Exception as e:
        print(f"[POST] Error: {e}")

    # 2. Try POST empty
    try:
        data = json.dumps({}).encode()
        req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            code = r.getcode()
            body = r.read().decode()
            print(f"[POST-Empty] Status: {code}")
            # print(body[:100])
    except Exception as e: pass

    # 3. Try GET
    try:
        req = urllib.request.Request(URL, headers=headers, method="GET")
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            code = r.getcode()
            body = r.read().decode()
            print(f"[GET] Status: {code}")
            print(f"Body Start: {body[:300]}")
            if "list" in body and code == 200:
                print("\n>>> RESULT: SUCCESS (List Found via GET)")
                return
    except urllib.error.HTTPError as e:
        print(f"[GET] Failed: {e.code}")
    except Exception as e:
        print(f"[GET] Error: {e}")

if __name__ == "__main__":
    check()

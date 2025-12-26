import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL_ACTION = "https://api.adw.net"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

kw_list = ["keyword1", "keyword2", "keyword3"]

payload = {
    "name": "Debug Test Link",
    "offer": "247_nurse", # Using a known offer? Or should I fetch one first?
    "site_key": "default_site", 
    "title": "Debug Title",
    "referrerAdCreative": "debug_creative",
    "keywords": kw_list,
    "postback": "s2s",
    "pixel_token": "https://skrotrack.com/postback?clickId={clickid}&payout={revenue}",
    "pixel_event": "lead"
}

print(f"Sending payload: {json.dumps(payload, indent=2)}")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0" # Sometimes APIs block default urllib UA
}

req = urllib.request.Request(f"{URL_ACTION}/panel/link_create", data=json.dumps(payload).encode(), headers=headers)

try:
    with urllib.request.urlopen(req, context=ctx) as r:
        raw = r.read().decode()
        print(f"Raw Response: '{raw}'")
        parsed = json.loads(raw)
        print("Parsed JSON:", parsed)
except Exception as e:
    print(f"Error: {e}")

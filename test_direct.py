# Test with direct field
import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Trying with a site value
payload = {
    "name": "TEST_WITH_SITE",
    "offer": "247_nurse",
    "title": "TEST_WITH_SITE",
    "keywords": ["test", "direct", "site"],
    "postback": "s2s",
    "pixel_token": "https://s2s.skro.eu/postback?clickid={clickid}&payout={revenue}",
    "pixel_event": "lead",
    "referrerAdCreative": "organic",
    "direct": "default_site"  # Try with a value
}

url = "https://api.adw.net/panel/link_create"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("Testing with direct='default_site'...")
try:
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        body = resp.read().decode('utf-8')
        print("Raw:", body[:500])
        # Find JSON part
        json_start = body.find('{')
        if json_start >= 0:
            result = json.loads(body[json_start:])
            print("\nResult:", json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")

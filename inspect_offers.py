import urllib.request
import json
import ssl

TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"
URL = "https://api.adw.net/panel/offer/list"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}
try:
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read().decode())
        print(json.dumps(data, indent=2))
except Exception as e:
    print(e)

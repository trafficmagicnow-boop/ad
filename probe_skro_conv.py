import urllib.request
import urllib.error
import json
import ssl

SKRO_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjkxNTksImFpZCI6OTAzMiwiZGlkIjoiIiwicmlkIjoxLCJhcHAiOjIsImlhdCI6MTc1NTg5NjYwNCwiZXhwIjoxNzg3NDMyNjA0LCJNYXBDbGFpbXMiOnt9fQ.Gbfih0c-OwVeWVEAMrW-Xn0wu9oWCuBu7qcmv94PKJ6mS56tKEKpUw8YFBrkpIHorOvQqC-pqaHGT_Saj3ad0ONAjLktlIOct_TapIOzVjwU1VFExGRtw0EZdq79bJA8prv3pzjq1KCaxaLuXfRJEblgpcztYNm5_1SCPTESxjy7j_GTliOWTIcBSX5Zc5piFETfxg038p4ahZTmIuPlMtGSiNTgOKWRXFeeDYhmNd9snW0g6tSLfi0jDrb_c2b4cf4NLww20dHZZnmdukiw7T1KITSjw11f2P-3QJTVWvn0B1pRlqNJF6c6R8WJCrAF0ODwTeNjKNmPQbPZVnHmwg"
BASE_URL = "https://api.skro.eu/api/v1"

def probe_conversions():
    headers = {
        "Authorization": f"Bearer {SKRO_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("--- Probing Skro Conversion Endpoints ---")
    
    # Endpoints to try
    endpoints = [
        "/conversions", 
        "/conversion", 
        "/events", 
        "/upload/conversions",
        "/custom_conversions"
    ]
    
    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        try:
            print(f"Checking {url} ...")
            # Try GET and POST (dry run)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                print(f"  [GET] Status: {response.getcode()}")
                print(f"  Response: {str(response.read())[:100]}")
        except urllib.error.HTTPError as e:
            print(f"  [GET] {ep} -> Error: {e.code}")
            # If 405 Method Not Allowed, valid endpoint but needs POST
            if e.code == 405:
                print("    (Method Not Allowed - Likely a valid POST endpoint)")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    probe_conversions()

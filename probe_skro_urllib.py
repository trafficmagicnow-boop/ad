import urllib.request
import urllib.error
import json
import ssl

# User provided Skro Key (JWT)
SKRO_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjkxNTksImFpZCI6OTAzMiwiZGlkIjoiIiwicmlkIjoxLCJhcHAiOjIsImlhdCI6MTc1NTg5NjYwNCwiZXhwIjoxNzg3NDMyNjA0LCJNYXBDbGFpbXMiOnt9fQ.Gbfih0c-OwVeWVEAMrW-Xn0wu9oWCuBu7qcmv94PKJ6mS56tKEKpUw8YFBrkpIHorOvQqC-pqaHGT_Saj3ad0ONAjLktlIOct_TapIOzVjwU1VFExGRtw0EZdq79bJA8prv3pzjq1KCaxaLuXfRJEblgpcztYNm5_1SCPTESxjy7j_GTliOWTIcBSX5Zc5piFETfxg038p4ahZTmIuPlMtGSiNTgOKWRXFeeDYhmNd9snW0g6tSLfi0jDrb_c2b4cf4NLww20dHZZnmdukiw7T1KITSjw11f2P-3QJTVWvn0B1pRlqNJF6c6R8WJCrAF0ODwTeNjKNmPQbPZVnHmwg"

BASE_URLS_TO_TRY = [
    "https://api.skro.eu/api/v1",
    "https://api.skro.eu",
    "https://panel.skro.eu/api",
    "https://panel.skro.eu/api/v1"
]

def probe():
    headers = {
        "Authorization": f"Bearer {SKRO_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Python-Client"
    }
    
    # Create SSL context to ignore potential cert issues if needed, strictly for testing
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("--- Probing Skro API (urllib) ---")
    
    endpoints = ["/offers", "/campaigns", "/user", "/profile"]
    
    for base in BASE_URLS_TO_TRY:
        print(f"\nChecking Base URL: {base}")
        for ep in endpoints:
            url = f"{base}{ep}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                    print(f"  GET {url} ... Status: {response.getcode()}")
                    if response.getcode() == 200:
                        data = response.read().decode('utf-8')
                        print(f"    SUCCESS! Data: {data[:200]}")
                        return
                    
            except urllib.error.HTTPError as e:
                print(f"  GET {url} ... Error: {e.code}")
            except Exception as e:
                print(f"  GET {url} ... Failed: {e}")

if __name__ == "__main__":
    probe()

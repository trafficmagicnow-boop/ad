import requests
import json

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
        "Accept": "application/json"
    }

    print("--- Probing Skro API ---")
    
    # Try to list offers or campaigns on various endpoints
    endpoints = ["/offers", "/campaigns", "/user", "/profile", "/ref/offers"] # Guesses
    
    for base in BASE_URLS_TO_TRY:
        print(f"\nChecking Base URL: {base}")
        for ep in endpoints:
            url = f"{base}{ep}"
            try:
                print(f"  GET {url} ...", end=" ")
                resp = requests.get(url, headers=headers, timeout=5)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"    SUCCESS! Found endpoint.")
                    try:
                        data = resp.json()
                        # print sample
                        print(f"    Sample Data: {str(data)[:200]}")
                        return base # Found a working base
                    except:
                        print("    (Not JSON)")
                elif resp.status_code == 401:
                    print("    (Unauthorized - Key might be invalid for this realm)")
            except Exception as e:
                print(f"    (Error: {e})")

    return None

if __name__ == "__main__":
    probe()

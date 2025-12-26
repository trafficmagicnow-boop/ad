# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import urllib.error
import json
import ssl

print("="*60)
print("  ADW/SKRO INTEGRATION - TEST")
print("="*60)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "http://localhost:8000"
TOKEN = "5a4fb29a30fb14b3c7bbea8333056f86"

def test_request(name, url, method='GET', data=None):
    print(f"\n[TEST] {name}")
    try:
        headers = {'Content-Type': 'application/json'}
        req_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            print(f"  [OK] Status: {resp.status}")
            
            try:
                parsed = json.loads(body)
                print(f"  [OK] JSON Response (length: {len(str(parsed))})")
                return parsed
            except:
                print(f"  [OK] HTML Response (length: {len(body)})")
                return body
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None

# Test 1: Dashboard
result = test_request("Dashboard", f"{BASE_URL}/")
if result and "Adw" in str(result):
    print("  [+] Dashboard OK")

# Test 2: API Data
result = test_request("API Data", f"{BASE_URL}/api/data")
if result and isinstance(result, dict):
    print(f"  [+] Offers: {len(result.get('offers', []))}, Articles: {len(result.get('articles', []))}")

# Test 3: Status
result = test_request("Status", f"{BASE_URL}/api/status")
if result and 'last_sync' in result:
    print(f"  [+] Last sync: {result['last_sync']}")

print("\n" + "="*60)
print("LINK CREATION TEST")
print("="*60)

# Test 4: Create Link
payload = {
    "name": "TEST_INTEGRATION_01",
    "title": "TEST_INTEGRATION_01",
    "offer": "247_nurse",
    "keywords": "test,qa",
    "postback_type": "s2s"
}

result = test_request("Create Link", f"{BASE_URL}/api/create_link", 'POST', payload)
if result and result.get('status') == 'ok':
    print(f"  [+] Link Created!")
    print(f"  [+] URL: {result.get('url', '')[:80]}")
    print(f"  [+] ID: {result.get('api_id')}")
    print(f"  [+] Status: {result.get('api_status')}")
    if '{clickid}' in result.get('url', ''):
        print("  [+] Skro clickid placeholder FOUND")
    else:
        print("  [!] WARNING: clickid placeholder MISSING")
else:
    print(f"  [FAIL] Link creation failed: {result}")

# Test 5: History
result = test_request("History", f"{BASE_URL}/api/list_links", 'POST', {})
if result and result.get('status') == 'ok':
    links = result.get('links', [])
    print(f"  [+] Found {len(links)} link(s)")

# Test 6: Stats
result = test_request("Stats", f"{BASE_URL}/api/get_stats", 'POST', {})
if result and result.get('status') == 'ok':
    print(f"  [+] Stats API OK")

print("\n" + "="*60)
print("REAL API TESTS")
print("="*60)

# Test 7: Real Adw API
try:
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"date_start": "01.01.2025", "date_end": "26.12.2025", "groups": ["time"], "timezone": "Europe/Kyiv"}
    req = urllib.request.Request("https://api.adw.net/panel/stats", 
                                 data=json.dumps(payload).encode('utf-8'), 
                                 headers=headers, method='POST')
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        r = json.loads(resp.read().decode('utf-8'))
        print(f"[TEST] Adw API Direct")
        print(f"  [OK] Status: {r.get('status')}")
        if r.get('status') == 'ok':
            print(f"  [+] ADW TOKEN IS VALID!")
except Exception as e:
    print(f"  [FAIL] Adw API: {e}")

# Test 8: Skro Postback
try:
    req = urllib.request.Request("https://s2s.skro.eu/postback?clickid=TEST999&payout=0.01&txt=test")
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        print(f"[TEST] Skro Postback")
        print(f"  [OK] Response: {resp.status}")
        print(f"  [+] SKRO ENDPOINT IS REACHABLE!")
except Exception as e:
    print(f"  [FAIL] Skro: {e}")

print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("""
All tests completed. Check results above.
If you see [+] marks, everything works!
If you see [FAIL], there's an issue.

KEY POINTS TO CHECK:
1. Dashboard loads
2. Link creation returns 'ok' status
3. URL contains {clickid} placeholder
4. Adw API token is valid
5. Skro postback endpoint reachable
""")

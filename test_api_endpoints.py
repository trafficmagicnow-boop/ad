"""
API Endpoint Validation Script
Tests all server endpoints to ensure they work correctly
"""
import urllib.request
import json
import ssl

# Disable SSL verification for local testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n🔍 Testing: {description or path}")
    print(f"   Method: {method}, URL: {url}")
    
    try:
        if method == "GET":
            req = urllib.request.Request(url, method="GET")
        else:  # POST
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode() if data else None,
                headers=headers,
                method="POST"
            )
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            body = response.read().decode()
            status = response.status
            
            # Try to parse as JSON
            try:
                data = json.loads(body)
                print(f"   ✅ Status: {status}")
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                return True, data
            except:
                print(f"   ✅ Status: {status}")
                print(f"   Response: {body[:200]}...")
                return True, body
                
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"   Error body: {error_body[:200]}")
        except:
            pass
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def run_tests():
    """Run all endpoint tests"""
    print("=" * 60)
    print("🚀 STARTING API ENDPOINT VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Test 1: GET /api/data
    success, _ = test_endpoint(
        "GET", "/api/data",
        description="Get offers and articles"
    )
    results.append(("GET /api/data", success))
    
    # Test 2: GET /api/status
    success, _ = test_endpoint(
        "GET", "/api/status",
        description="Get sync status"
    )
    results.append(("GET /api/status", success))
    
    # Test 3: GET / (Dashboard)
    success, _ = test_endpoint(
        "GET", "/",
        description="Load dashboard HTML"
    )
    results.append(("GET /", success))
    
    # Test 4: POST /api/create_link
    test_data = {
        "name": "Test Campaign API Validation",
        "offer": "247_nurse",
        "article": "test_site",
        "title": "Test Title",
        "keywords": "test1,test2,test3",
        "postback_type": "s2s",
        "referrerAdCreative": "api_test"
    }
    success, resp = test_endpoint(
        "POST", "/api/create_link",
        data=test_data,
        description="Create link (S2S)"
    )
    results.append(("POST /api/create_link", success))
    
    # Test 5: POST /api/list_links
    success, _ = test_endpoint(
        "POST", "/api/list_links",
        description="Get link history"
    )
    results.append(("POST /api/list_links", success))
    
    # Test 6: POST /api/get_stats
    success, _ = test_endpoint(
        "POST", "/api/get_stats",
        description="Get raw stats"
    )
    results.append(("POST /api/get_stats", success))
    
    # Test 7: POST /api/sync
    success, _ = test_endpoint(
        "POST", "/api/sync",
        description="Manual sync trigger"
    )
    results.append(("POST /api/sync", success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {endpoint}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Check logs above")
    
    return passed == total

if __name__ == "__main__":
    # Note: Run server.py first with: python server.py
    print("Make sure server.py is running on localhost:8000")
    input("Press Enter to start tests...")
    
    success = run_tests()
    exit(0 if success else 1)

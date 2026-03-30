import requests, json, uuid

BASE = "http://localhost:8082" # Using root because mappings don't have 2.0
HEADERS = {"Authorization": "Bearer fake-token", "x-request-id": str(uuid.uuid4())}

def inspect(test_name, method, path):
    # Using Api-Scenario as primary, adding x-test-name for compatibility
    h = {**HEADERS, "Api-Scenario": test_name, "x-test-name": test_name}
    url = f"{BASE}{path}"
    print(f"\n{'='*50}")
    print(f"TEST: {test_name} | {method} {path} | URL: {url}")
    
    try:
        r = requests.request(method, url, headers=h, timeout=5)
        print(f"STATUS: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Print a concise version of the JSON
            print(json.dumps(data, indent=2)[:2000]) 
        else:
            print(f"Error Response: {r.text[:500]}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Run ALL key operations — using names found in Phase 1
    inspect("List Sheets - No Params",     "GET",  "/sheets")
    inspect("Assume User - Can Be Set",     "GET",  "/sheets/123")
    
    # These might fail (404) if mappings don't exist yet, we'll add them in Step 5
    inspect("Update Rows - Location - Top", "PUT",  "/sheets/123/rows")
    inspect("Serialization - Discussion",   "POST", "/sheets/123/discussions")
    inspect("Serialization - Column",       "POST", "/sheets/123/columns")
    inspect("Serialization - Sheet",        "POST", "/sheets")

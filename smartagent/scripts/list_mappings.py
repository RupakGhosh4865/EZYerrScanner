import os, json

def list_all_mappings(mappings_dir="smartsheet-sdk-tests/mappings"):
    """
    Walks the mappings directory and prints every available test name.
    Run this to know exactly which x-test-name values you can use.
    """
    mappings = []
    if not os.path.exists(mappings_dir):
        print(f"Error: Mappings directory not found at {mappings_dir}")
        print("Run: bash scripts/start_mock_server.sh first.")
        return

    for root, dirs, files in os.walk(mappings_dir):
        for fname in files:
            if fname.endswith(".json"):
                path = os.path.join(root, fname)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    
                    # Each mapping file has a "request" and "response" block
                    req = data.get("request", {})
                    headers = req.get("headers", {})
                    
                    # Try both Api-Scenario and x-test-name
                    test_name_header = headers.get("Api-Scenario", headers.get("x-test-name", {}))
                    test_name = test_name_header.get("equalTo", "no-test-name")
                    method = req.get("method", "?")
                    url_pattern = req.get("url", req.get("urlPattern", req.get("urlPathPattern", "?")))
                    
                    mappings.append({
                        "test_name": test_name,
                        "method": method,
                        "url": url_pattern,
                        "file": path.replace("smartsheet-sdk-tests/", "")
                    })
                except Exception as e:
                    print(f"Error parsing {path}: {e}")
    
    mappings.sort(key=lambda x: x["test_name"])
    print(f"Found {len(mappings)} mappings:\n")
    for m in mappings:
        print(f"  x-test-name: '{m['test_name']}'")
        print(f"    {m['method']} {m['url']}")
        print(f"    File: {m['file']}\n")

if __name__ == "__main__":
    list_all_mappings()

import requests, json

ADMIN = "http://localhost:8082/__admin"

def list_loaded_mappings():
    """Shows all mappings currently loaded in WireMock."""
    try:
        r = requests.get(f"{ADMIN}/mappings")
        data = r.json()
        print(f"Total mappings loaded: {data['meta']['total']}")
        for m in data["mappings"]:
            req = m.get("request", {})
            headers = req.get("headers", {})
            # Try to find scenario name
            scenario = headers.get("Api-Scenario", headers.get("x-test-name", {}))
            name = scenario.get("equalTo", "no-test-name")
            print(f"  {req.get('method','?')} {req.get('urlPathPattern', req.get('url','?'))} | Scenario: {name}")
    except Exception as e:
        print(f"Failed to list mappings: {e}")

def see_recent_requests():
    """Shows the last 10 requests WireMock received — great for debugging."""
    try:
        r = requests.get(f"{ADMIN}/requests?limit=10")
        data = r.json()
        print(f"\nRecent requests ({data['meta']['total']} total):")
        for req_item in data["requests"]:
            req = req_item.get("request", {})
            matched = req_item.get("wasMatched", False)
            print(f"  {'[MATCHED]' if matched else '[UNMATCHED]'} {req.get('method')} {req.get('url')}")
            headers = req.get("headers", {})
            print(f"    Api-Scenario: {headers.get('Api-Scenario', 'MISSING')}")
    except Exception as e:
        print(f"Failed to see recent requests: {e}")

if __name__ == "__main__":
    list_loaded_mappings()
    see_recent_requests()

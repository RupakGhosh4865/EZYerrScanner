import smartsheet
import os
import json
import requests

# CONFIG
WIREMOCK_URL = "http://localhost:8082"
TEST_NAME = "list-sheets"

def debug_sdk_call():
    print(f"Connecting to WireMock at {WIREMOCK_URL}...")
    
    # Initialize real SDK pointed at WireMock
    # This is what MockSmartsheetClient does internally
    client = smartsheet.Smartsheet(
        access_token="fake-token",
        api_base=f"{WIREMOCK_URL}/2.0"
    )
    
    # Manual check of what WireMock returns before the SDK parses it
    print("\n--- RAW HTTP CHECK ---")
    try:
        raw_res = requests.get(f"{WIREMOCK_URL}/2.0/sheets")
        print(f"Status: {raw_res.status_code}")
        print(f"Headers: {raw_res.headers.get('Content-Type')}")
        print(f"Body snippet: {raw_res.text[:200]}")
    except Exception as e:
        print(f"Raw HTTP failed: {e}")

    print("\n--- SDK CALL ---")
    try:
        response = client.Sheets.list_sheets()
        print(f"SDK Response Type: {type(response)}")
        
        if hasattr(response, 'data'):
            print(f"SUCCESS! Found {len(response.data)} sheets.")
            for s in response.data:
                print(f" - Sheet: {s.name} (ID: {s.id})")
        else:
            print("FAILURE: Response object has no 'data' attribute.")
            if hasattr(response, 'result'):
                print(f"Error Code: {response.result.error_code}")
                print(f"Message: {response.result.message}")
            else:
                print(f"Response: {response}")

    except Exception as e:
        print(f"SDK Call crashed: {e}")

if __name__ == "__main__":
    debug_sdk_call()

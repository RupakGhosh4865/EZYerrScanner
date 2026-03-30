import requests
import os
import sys

# Add backend directory to path so Smartsheet SDK and mock_client can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

WIREMOCK_BASE = "http://localhost:8082"

def test_wiremock_alive():
    """Check if WireMock is running."""
    try:
        r = requests.get(f"{WIREMOCK_BASE}/__admin/mappings", timeout=3)
        data = r.json()
        total = data.get('meta', {}).get('total', data.get('total', 0))
        print(f"WireMock is alive. Loaded {total} mappings.")
        return True
    except Exception as e:
        print(f"WireMock not reachable: {e}")
        print("Run: bash scripts/start_mock_server.sh first.")
        return False

def test_list_sheets_via_sdk():
    """Call list_sheets through SDK pointed at WireMock."""
    from smartsheet_client.mock_client import MockSmartsheetClient
    
    print("\n--- Testing list_sheets via SDK ---")
    client = MockSmartsheetClient(test_name="List Sheets - No Params")
    try:
        response = client.Sheets.list_sheets()
        print(f"list_sheets response type: {type(response)}")
        print(f"Number of sheets returned: {len(response.data)}")
        for sheet in response.data:
            print(f"  Sheet: id={sheet.id}, name={sheet.name}")
    except Exception as e:
        print(f"Error in list_sheets: {e}")

def test_get_sheet_via_sdk():
    """Call get_sheet through SDK pointed at WireMock."""
    from smartsheet_client.mock_client import MockSmartsheetClient
    
    print("\n--- Testing get_sheet via SDK ---")
    client = MockSmartsheetClient(test_name="Assume User - Can Be Set")
    try:
        # Use ID from the mapping (123)
        response = client.Sheets.get_sheet(123)
        
        print(f"get_sheet response: {response.name}")
        print(f"Total rows: {response.total_row_count}")
        print(f"Columns: {[c.title for c in response.columns]}")
        if response.rows:
            first_row = response.rows[0]
            print(f"First row cells: {[c.value for c in first_row.cells]}")
    except Exception as e:
        print(f"Error in get_sheet: {e}")

if __name__ == "__main__":
    alive = test_wiremock_alive()
    if alive:
        test_list_sheets_via_sdk()
        test_get_sheet_via_sdk()

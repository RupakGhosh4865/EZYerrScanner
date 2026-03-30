import smartsheet
import uuid
import os

class MockSmartsheetClient:
    # Map internal shorthand names to WireMock scenario names
    SCENARIO_MAP = {
        "list-sheets": "List Sheets - No Params",
        "get-sheet": "Get Sheet",
        "add-comment": "Add Comment to Row",
        "flag-cell": "Update Rows - Location - Top",
        "create-sheet": "Create Sheet in Folder",
    }
    def __init__(self, test_name: str = "default"):
        self.test_name = test_name
        self.request_id = str(uuid.uuid4())
        
        mock_url = os.getenv("SMARTSHEET_MOCK_URL", "http://localhost:8082").rstrip("/")

        # Point SDK at WireMock instead of real Smartsheet
        self.client = smartsheet.Smartsheet(
            access_token="fake-token-for-wiremock",
            api_base=mock_url
        )
        self.client.errors_as_exceptions(True)
        self.set_test_name(test_name)
    
    def set_test_name(self, name: str):
        """Call this before each SDK operation to route to the right mapping."""
        self.test_name = name
        self.request_id = str(uuid.uuid4())
        scenario = self.SCENARIO_MAP.get(name, name)
        
        # Use official SDK test methods instead of monkeypatching
        self.client.as_test_scenario(scenario)
        self.client.with_wiremock_test_case(scenario, self.request_id)
    
    @property
    def Sheets(self):
        return self.client.Sheets

    @property
    def Home(self):
        return self.client.Home

    @property
    def Discussions(self):
        return self.client.Discussions
    
    @property
    def Comments(self):
        return self.client.Comments

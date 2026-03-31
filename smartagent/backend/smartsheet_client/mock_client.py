import smartsheet
import uuid
import os

WIREMOCK_URL = os.getenv("SMARTSHEET_MOCK_URL", "http://localhost:8082")
SMARTSHEET_API_VERSION = "2.0"

class MockSmartsheetClient:
    """
    Wraps the official Smartsheet Python SDK and points it at WireMock.
    
    The SDK's Smartsheet() constructor accepts:
      - access_token: any non-empty string works with WireMock
      - api_base: the base URL to use instead of api.smartsheet.com
    
    We also inject the required WireMock headers into every request
    by subclassing the SDK's HTTP client.
    """
    
    def __init__(self, test_name: str = "default"):
        self.test_name = test_name
        self.request_id = str(uuid.uuid4())
        
        # Point SDK at WireMock instead of real Smartsheet
        # Ensure no trailing slash to avoid //2.0 pathing issues
        base_url = WIREMOCK_URL.rstrip('/')
        self.client = smartsheet.Smartsheet(
            access_token="fake-token-for-wiremock",
            # Smartsheet SDK expects api_base to include the API version path.
            api_base=f"{base_url}/{SMARTSHEET_API_VERSION}"
        )

        # Match real-client behavior: raise SDK exceptions on errors
        # (otherwise the SDK may return an Error object without .data)
        self.client.errors_as_exceptions(True)
        
        # Inject WireMock routing headers into the SDK's session
        self._inject_wiremock_headers()
    
    def _inject_wiremock_headers(self):
        """
        Smartsheet SDK sometimes resets headers. 
        We monkeypatch the session.request to ensure headers are injected.
        """
        session = self.client._session
        # Use a closure-friendly way to get the current test_name
        parent = self
        original_request = session.request
        
        def mock_request(method, url, **kwargs):
            # Ensure headers dict exists
            if 'headers' not in kwargs or kwargs['headers'] is None:
                kwargs['headers'] = {}
            
            # Inject required WireMock headers
            kwargs['headers']["Api-Scenario"] = parent.test_name
            kwargs['headers']["x-test-name"] = parent.test_name
            kwargs['headers']["x-request-id"] = parent.request_id
            kwargs['headers']["Authorization"] = f"Bearer {parent.request_id}"
            
            # Some versions of requests handle headers case-insensitively, 
            # but WireMock might be sensitive if using specific matching.
            return original_request(method, url, **kwargs)
            
        session.request = mock_request
    
    def set_test_name(self, name: str):
        """Call this before each SDK operation to route to the right mapping."""
        self.test_name = name
        self.request_id = str(uuid.uuid4())
    
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

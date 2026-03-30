import os

"""
ENVIRONMENT MODES
=================

Development (default — no Docker needed for backend):
  USE_MOCK_SERVER=true
  SMARTSHEET_MOCK_URL=http://localhost:8082
  → SDK points at WireMock running locally via Docker
  → No real Smartsheet account needed
  → All operations logged by WireMock admin at :8082/__admin
  → Start WireMock: cd smartsheet-sdk-tests && docker compose up -d

Docker Compose (all services together):
  USE_MOCK_SERVER=true
  SMARTSHEET_MOCK_URL=http://wiremock:8080   ← Docker internal network
  → Set automatically by docker-compose.yml environment block
  → Start everything: docker compose up (from project root)
  → WireMock admin still accessible at http://localhost:8082/__admin

Production (real Smartsheet API):
  USE_MOCK_SERVER=false
  SMARTSHEET_ACCESS_TOKEN=your_real_token_here
  → SDK points at https://api.smartsheet.com (default Smartsheet URL)
  → All write operations affect real data — HITL approval step is mandatory
  → Get a token: Smartsheet → Account → Personal Settings → API Access

To switch modes: change USE_MOCK_SERVER in backend/.env
No code changes required between any of the three environments.
"""


from dotenv import load_dotenv

# Load .env but do NOT override existing environment variables (important for Docker)
load_dotenv(override=False)

def get_smartsheet_client(test_name: str = "list-sheets"):
    """
    Factory: returns the correct Smartsheet client for the current environment.
    """
    use_mock = os.getenv("USE_MOCK_SERVER", "true").lower() == "true"
    
    # Priority: 1. ENV (Docker/Manual) -> 2. Docker default -> 3. Local default
    mock_url = os.getenv("SMARTSHEET_MOCK_URL")
    if not mock_url:
        is_docker = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
        mock_url = "http://wiremock:8080" if is_docker else "http://localhost:8082"

    if use_mock:
        print(f"DEBUG: SmartAgent using MOCK mode with URL: {mock_url}")
        from smartsheet_client.mock_client import MockSmartsheetClient
        return MockSmartsheetClient(test_name=test_name)

    # ── Real Smartsheet API ─────────────────────────────────────────────────
    import smartsheet
    token = os.getenv("SMARTSHEET_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError(
            "SMARTSHEET_ACCESS_TOKEN is not set. "
            "Set it in backend/.env or switch to mock mode with USE_MOCK_SERVER=true."
        )
    client = smartsheet.Smartsheet(access_token=token)
    client.errors_as_exceptions(True)
    return client

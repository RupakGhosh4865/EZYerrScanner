import requests
import json

r = requests.get('http://localhost:8082/__admin/requests')
requests_log = r.json()['requests']
if requests_log:
    last_req = requests_log[-1]['request']
    print(f"FAILED URL: [{last_req['url']}]")
    print(f"METHOD: {last_req['method']}")
    print(f"HEADERS: {json.dumps(last_req.get('headers', {}), indent=2)}")
else:
    print("No requests found in WireMock log.")

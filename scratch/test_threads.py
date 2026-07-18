import requests

url = "http://127.0.0.1:8000/api/copilotkit/threads"

# Try with no body
try:
    response = requests.post(url)
    print(f"No body POST status: {response.status_code}")
    print(f"No body POST response: {response.text}")
except Exception as e:
    print(f"No body error: {e}")

# Try with empty JSON body
try:
    response = requests.post(url, json={})
    print(f"Empty JSON POST status: {response.status_code}")
    print(f"Empty JSON POST response: {response.text}")
except Exception as e:
    print(f"Empty JSON error: {e}")

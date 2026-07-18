import requests
import json

url = "http://127.0.0.1:8000/api/copilotkit/agent/default"

payload = {
    "state": {"current_step": "EXTRACTING"},
    "messages": [{"id": "1", "role": "user", "content": "hi"}],
    "threadId": "verification-thread-id-v2"
}

print("Testing V2 agent execute endpoint...")
try:
    response = requests.post(url, json=payload, stream=True)
    print(f"Status Code: {response.status_code}")
    print("Response headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
        
    print("\nResponse stream chunks:")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(f"Error calling backend: {e}")

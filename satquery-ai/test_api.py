import urllib.request
import json
import urllib.error

payload = {
    'latitude': 28.0,
    'longitude': 86.9,
    'radius_km': 10,
    'monitoring_type': 'flood',
    'frequency': 'daily'
}

print("[1] Testing server health...")
try:
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/health'), timeout=3) as f:
        print("Health OK.")
except Exception as e:
    print("Health check failed:", str(e))

print("[2] Starting monitoring...")
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/monitoring/start', data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req, timeout=15) as f:
        print("[3] Response received:")
        print(json.dumps(json.loads(f.read().decode('utf-8')), indent=2))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Error:", str(e))

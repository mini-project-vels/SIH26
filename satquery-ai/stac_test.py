import urllib.request
import json
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/monitoring/debug?latitude=52.0&longitude=5.5')
    with urllib.request.urlopen(req) as f:
        print(json.dumps(json.loads(f.read().decode('utf-8')), indent=2))
except Exception as e:
    print(str(e))
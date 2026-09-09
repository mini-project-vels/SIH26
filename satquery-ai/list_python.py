import subprocess
import json
try:
    cmd = 'powershell -Command "Get-CimInstance Win32_Process -Filter \\"Name=\'python.exe\'\\" | Select-Object ProcessId, CommandLine | ConvertTo-Json"'
    res = subprocess.check_output(cmd, shell=True)
    out = res.decode('utf-8', errors='ignore')
    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]
    for p in data:
        pid = p.get('ProcessId')
        cmdline = p.get('CommandLine') or ""
        if "uvicorn" in cmdline or "main:app" in cmdline:
            print(f"UVICORN_PID: {pid}")
except Exception as e:
    print("FAILED:", e)

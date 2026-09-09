content = open('test_featherless.log', encoding='utf-16').read()
lines = content.splitlines()
for l in lines:
    if "Qwen2.5-VL-7B-Instruct" in l:
        prov = "auto"
        if ":" in l:
            prov = l.split("Testing ")[1].split(" ...")[0].split(":")[-1]
        
        status = "OK"
        if "FAILED" in l:
            status = l.split("FAILED: ")[1][:60]
        elif "invalid provider" in l:
            status = "invalid provider"
        elif "no provider" in l:
            status = "no provider enabled"
        print(f"{prov}: {status}")

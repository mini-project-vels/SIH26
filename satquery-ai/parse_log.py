lines = open('test_featherless.log', encoding='utf-16').read().splitlines()
for l in lines:
    if "Testing" in l:
        parts = l.split("Testing ")
        if len(parts) > 1:
            m = parts[1].split(" ...")[0]
            m_short = m.replace("Qwen/Qwen2.5-VL-", "Qwen").replace("meta-llama/Llama-3.2-", "Llama").replace("microsoft/Phi-3.5-", "Phi").replace("-Instruct", "").replace("-instruct", "").replace("-Vision", "")
            res = "OK" if "SUCCESS" in l else ("INV" if "invalid" in l else "NO_PROV" if "no provider" in l else "FAIL")
            print(f"{m_short}: {res}")

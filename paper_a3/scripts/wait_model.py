# -*- coding: utf-8 -*-
r"""Wait until the LM Studio OpenAI API lists a model whose id contains the given substring."""
import json
import sys
import time
import urllib.request

needle, timeout = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 900
deadline = time.time() + timeout
while time.time() < deadline:
    try:
        with urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=10) as r:
            ids = [m.get("id", "") for m in json.loads(r.read()).get("data", [])]
        if any(needle in i for i in ids):
            print("model ready:", [i for i in ids if needle in i])
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception:
        pass
    time.sleep(15)
print("timeout waiting for", needle)
raise SystemExit(1)

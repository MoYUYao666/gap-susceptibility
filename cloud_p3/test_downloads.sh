#!/bin/bash
echo "== curl dolly from hf-mirror =="
curl -s -L -m 40 -o /root/autodl-tmp/p3work/dolly_test.jsonl -w "http=%{http_code} size=%{size_download} speed=%{speed_download}\n" \
  "https://hf-mirror.com/datasets/databricks/databricks-dolly-15k/resolve/main/databricks-dolly-15k.jsonl" || echo CURL_FAIL
ls -la /root/autodl-tmp/p3work/dolly_test.jsonl 2>/dev/null
echo "== modelscope repos =="
/root/miniconda3/bin/python - <<'PY'
from modelscope.hub.api import HubApi
api = HubApi()
for kind, fn in (("model", api.get_model_files), ("dataset", getattr(api, "get_dataset_files", None))):
    for repo in ("AI-ModelScope/databricks-dolly-15k", "databricks/databricks-dolly-15k",
                 "llava-hf/llava-onevision-qwen2-0.5b-instruct-hf",
                 "AI-ModelScope/llava-onevision-qwen2-0.5b-instruct-hf",
                 "Qwen/Qwen2-VL-2B-Instruct"):
        try:
            files = fn(repo)
            print(kind, repo, "OK", len(files))
        except Exception as e:
            print(kind, repo, "ERR", str(e)[:70])
PY

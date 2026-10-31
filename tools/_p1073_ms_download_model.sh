#!/usr/bin/env bash
# Download the LLaVA weights from ModelScope, with a reachability check first.
#
# Context: on this host download.pytorch.org stalled at 0 B/s, huggingface.co is unreachable, and hf-mirror.com
# answered slowly. ModelScope is the domestic source the project lists first. This checks that modelscope.cn is
# actually reachable from the container, then pulls the weights and reports the achieved rate.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export MODELSCOPE_CACHE=/root/autodl-tmp/modelscope
PY=/root/miniconda3/bin/python
mkdir -p "$MODELSCOPE_CACHE"

echo "=== reachability ==="
curl -sS -m 15 -o /dev/null -w '  modelscope.cn          %{http_code}  %{speed_download} B/s\n' https://www.modelscope.cn/ 2>/dev/null || echo "  modelscope.cn unreachable"
curl -sS -m 15 -o /dev/null -w '  modelscope api         %{http_code}  %{speed_download} B/s\n' https://www.modelscope.cn/api/v1/models/AI-ModelScope/llava-1.5-7b-hf 2>/dev/null || echo "  api unreachable"
curl -sS -m 15 -o /dev/null -w '  modelscope files host  %{http_code}  %{speed_download} B/s\n' https://modelscope.cn/ 2>/dev/null || echo "  files host unreachable"

echo "=== candidate model listing via HubApi (no datasets import) ==="
$PY - <<'PYEOF'
from modelscope.hub.api import HubApi
api = HubApi()
for repo in ("AI-ModelScope/llava-1.5-7b-hf", "llava-hf/llava-1.5-7b-hf",
             "AI-ModelScope/llava-v1.5-7b", "Qwen/Qwen2-VL-2B-Instruct"):
    try:
        files = api.get_model_files(repo, recursive=True)
        total = sum((f.get("Size") or 0) for f in files)
        print(f"  OK   {repo:<38} {len(files)} files  {total/1e9:.2f} GB")
    except Exception as exc:
        print(f"  FAIL {repo:<38} {type(exc).__name__}: {str(exc)[:64]}")
PYEOF

echo "=== download the weights ==="
$PY - <<'PYEOF'
import os, time
from modelscope import snapshot_download
t0 = time.time()
try:
    p = snapshot_download("AI-ModelScope/llava-1.5-7b-hf", cache_dir="/root/autodl-tmp/modelscope")
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _d, fs in os.walk(p) for f in fs)
    dt = time.time() - t0
    print("  path:", p)
    print("  size %.2f GB in %.0f s (%.2f MB/s)" % (size/1e9, dt, size/1e6/max(dt, 1)))
except Exception as exc:
    print("  FAILED:", type(exc).__name__, str(exc)[:200])
PYEOF

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
du -sh /root/autodl-tmp/modelscope 2>/dev/null
echo MS_MODEL_DONE

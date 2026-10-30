#!/usr/bin/env bash
# Use ModelScope, which is the fast source for a mainland host: install the client and confirm the exact
# repository names before downloading anything large.
#
# Why: on this instance download.pytorch.org delivered 0 B/s and huggingface.co is unreachable; the mirror
# (hf-mirror.com) answered but slowly. ModelScope is the domestic source the project's own guidance lists
# first, and it also carries the COCO dataset, which matters because images.cocodataset.org is giving about
# 400 B/s for the annotation archive here.
set -uo pipefail
cd /root/p3
export PYTHONIOENCODING=utf-8
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
PY=/root/miniconda3/bin/python

echo "=== stop stalled installs ==="
pkill -9 -f "pip install" || true
sleep 2
ps -eo pid,cmd | grep "pip install" | grep -v grep || echo "  none running"

echo "=== install modelscope from tuna ==="
$PY -m pip install -q --no-input -i https://pypi.tuna.tsinghua.edu.cn/simple \
    modelscope "huggingface_hub[hf_transfer]" hf_transfer 2>&1 | tail -3
$PY -c "import modelscope; print('  modelscope', modelscope.__version__)"

echo "=== ModelScope API reachability and candidate repos ==="
$PY - <<'PYEOF'
import json, urllib.request, urllib.parse

def api(path):
    url = "https://www.modelscope.cn/api/v1/" + path
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}

for label, path in (
    ("models search llava", "models?PageSize=10&Name=" + urllib.parse.quote("llava")),
    ("datasets search coco", "datasets?PageSize=10&Name=" + urllib.parse.quote("coco")),
):
    data = api(path)
    if "_error" in data:
        print(f"  {label}: FAILED {data['_error']}")
        continue
    items = data.get("Data", {}).get("Models") or data.get("Data", {}).get("Datasets") or []
    ids = [i.get("Path") or i.get("Name") or (i.get("Owner", "") + "/" + i.get("Name", "")) for i in items[:10]]
    print(f"  {label}: {ids}")
PYEOF
echo DIAG2_DONE

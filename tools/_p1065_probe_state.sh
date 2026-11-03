#!/usr/bin/env bash
# Report the host's state: what is installed, whether the stalled downloads are moving, and what the network
# can actually reach. Everything here is read-only.
set -uo pipefail
echo "=== key imports ==="
/root/miniconda3/bin/python - <<'PYEOF'
import importlib
for m in ("torch", "torchvision", "transformers", "peft", "accelerate", "numpy", "PIL",
          "huggingface_hub", "hf_transfer"):
    try:
        mod = importlib.import_module(m)
        print("  %-16s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as exc:
        print("  %-16s MISSING (%s)" % (m, type(exc).__name__))
PYEOF

echo "=== installs still running ==="
ps -eo pid,etimes,cmd | grep -E "pip|python" | grep -v grep | head -5 || echo none

echo "=== sizes (30 s apart) ==="
A1=$(stat -c %s /root/p3/coco_eval/_ann.zip 2>/dev/null || echo 0)
B1=$(du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1 || echo 0)
sleep 30
A2=$(stat -c %s /root/p3/coco_eval/_ann.zip 2>/dev/null || echo 0)
B2=$(du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1 || echo 0)
echo "  coco annotation zip: $A1 -> $A2  ($(( (A2-A1)/30 )) B/s)"
echo "  pip cache:           $B1 -> $B2  ($(( (B2-B1)/30 )) B/s)"

echo "=== mirrors ==="
curl -sS -m 15 -o /dev/null -w '  tuna      %{http_code}  %{speed_download} B/s\n' https://pypi.tuna.tsinghua.edu.cn/simple/ 2>/dev/null || echo "  tuna unreachable"
curl -sS -m 15 -o /dev/null -w '  aliyun    %{http_code}  %{speed_download} B/s\n' https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || echo "  aliyun unreachable"
curl -sS -m 15 -o /dev/null -w '  hf-mirror %{http_code}  %{speed_download} B/s\n' https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json 2>/dev/null || echo "  hf-mirror unreachable"
curl -sS -m 15 -o /dev/null -w '  coco      %{http_code}  %{speed_download} B/s\n' http://images.cocodataset.org/val2014/COCO_val2014_000000000139.jpg 2>/dev/null || echo "  coco unreachable"

echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo PROBE_DONE

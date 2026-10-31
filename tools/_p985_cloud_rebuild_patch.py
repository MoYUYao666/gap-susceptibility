# -*- coding: utf-8 -*-
r"""Freeze the cloud fixes into one local, re-runnable script.

The rented host became unreachable on 2026-10-15 at about 23:52, while the bf16 sweep was at step 650 of
2250. The cloud-side knowledge is the expensive part, so it is captured here:

* `torchvision==0.24.1` for cu130 -- the image ships 0.27.1, which is built against a different torch and
  makes `import transformers`/`import peft` fail with "operator torchvision::nms does not exist";
* the pinned stack -- torch 2.9.1+cu130, transformers 5.16.1, peft 0.20.0, bitsandbytes 0.50.2,
  accelerate 1.14.0, datasets 5.0.1, pillow 12.3.0, numpy 2.5.2;
* no `prepare_model_for_kbit_training` in bf16 -- it upcasts every parameter to fp32, which took the 15 GB
  model to 30 GB and died with CUDA out of memory;
* kill the previous run and **verify** the memory came back before loading, because `pkill` returned while
  the old process still held 29.24 GiB;
* no `tee` in the pipeline, because it buffers and hides the heartbeats.

    python tools/_p985_cloud_rebuild_patch.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "SUBMISSION" / "cloud_p3_setup.sh"
SWEEP = REPO / "tools" / "_p820_llava_sites.py"

SCRIPT = r"""#!/usr/bin/env bash
# Rebuild the P3 LLaVA sweep on a fresh rented GPU host. Frozen 2026-10-15 after the first host went away.
# Usage: scp this file and tools/_p820_llava_sites.py to the host, then: bash cloud_p3_setup.sh <N_IMAGES>
set -uo pipefail
N=${1:-2000}                        # images to use: N-500 train, 500 held out
WORK=/root/p3
COCO=$WORK/coco_full
PY=/root/miniconda3/bin/python
export HF_HOME=/root/autodl-tmp/hf
export PIP_CACHE_DIR=/root/autodl-tmp/pipcache
mkdir -p "$WORK/tools" "$HF_HOME" "$COCO/annotations" "$COCO/val2014"

echo "=== 1. pinned stack ==="
$PY -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true
$PY -m pip install --no-input "numpy==2.5.2" "pillow==12.3.0" 2>&1 | tail -2
$PY -m pip install --no-input "torch==2.9.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -3
# torchvision MUST match torch: the image's own build breaks transformers with
# "RuntimeError: operator torchvision::nms does not exist".
$PY -m pip install --no-input "torchvision==0.24.1" --index-url https://download.pytorch.org/whl/cu130 2>&1 | tail -3
$PY -m pip install --no-input "transformers==5.16.1" "peft==0.20.0" "accelerate==1.14.0" \
    "bitsandbytes==0.50.2" "datasets==5.0.1" sentencepiece protobuf 2>&1 | tail -4

echo "=== 2. prove every import works (version numbers alone are not enough) ==="
$PY - <<'EOF'
import importlib, sys
want = {"torch": "2.9.1", "torchvision": "0.24.1", "transformers": "5.16.1", "peft": "0.20.0",
        "bitsandbytes": "0.50.2", "accelerate": "1.14.0"}
bad = []
for name, ver in want.items():
    try:
        got = getattr(importlib.import_module(name), "__version__", "?")
    except Exception as exc:
        got = "BROKEN:%s" % type(exc).__name__
    ok = str(got).startswith(ver)
    print("  %-3s %-14s %s (want %s)" % ("OK" if ok else "BAD", name, got, ver))
    if not ok: bad.append(name)
if bad: sys.exit("IMPORTS BROKEN: " + ",".join(bad))
print("ALL_IMPORTS_OK")
EOF

echo "=== 3. model on the server (never uploaded) ==="
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HUB_DISABLE_XET=1
$PY -c "from huggingface_hub import snapshot_download; print(snapshot_download('llava-hf/llava-1.5-7b-hf'))"

echo "=== 4. data: official annotations + $N images (same order as local) ==="
ANN=$COCO/annotations/captions_val2014.json
if [ ! -f "$ANN" ]; then
  curl -sSL -o $COCO/ann.zip http://images.cocodataset.org/annotations/annotations_trainval2014.zip
  (cd $COCO && unzip -o -q ann.zip annotations/captions_val2014.json && rm -f ann.zip)
fi
$PY - <<PYEOF
import json
from pathlib import Path
N = $N
ann = json.loads(Path("$ANN").read_text(encoding="utf-8", errors="ignore"))
by = {}
for c in ann["annotations"]:
    by.setdefault(c["image_id"], []).append(c["caption"])
ids = list(by)[:N]
Path("$COCO/ids.txt").write_text("\n".join(str(i) for i in ids), encoding="utf-8")
base = "http://images.cocodataset.org/val2014/COCO_val2014_%012d.jpg"
Path("$COCO/urls.txt").write_text("\n".join(base % i for i in ids) + "\n", encoding="utf-8")
print("  ids:", len(ids))
PYEOF
(cd $COCO/val2014 && xargs -a $COCO/urls.txt -P 16 -n 1 -I{} sh -c 'f=$(basename {}); [ -s "$f" ] || curl -sS -o "$f" {}')
ls $COCO/val2014 | wc -l; du -sh $COCO/val2014

echo "=== 5. run (bf16, no quantisation, S train / 500 held out, 3 epochs, 3 seeds, 4 arms) ==="
S=$((N-500))
cd $WORK
pkill -9 -f _p820_llava_sites || true
for i in $(seq 1 30); do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  [ "$used" -lt 2000 ] && break
  echo "  waiting for the device: ${used} MiB still in use"; sleep 10
done
rm -rf outputs/llava_bf16_sites
$PY -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root "$COCO" --precision bf16 \
  --samples "$S" --eval-pairs 500 --epochs 3 \
  --batch 2 --max-len 2048 --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 25 \
  --out-dir outputs/llava_bf16_sites 2>&1 | grep -Ev "Loading weights|it/s\]"
echo BF16_SWEEP_DONE
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  patch would be written to {OUT.relative_to(REPO).as_posix()} "
          f"({len(SCRIPT.splitlines())} lines)")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(SCRIPT)
    # a copy of the sweep next to it, so the pair can be sent to any fresh host
    dst = OUT.parent / "_p820_llava_sites.py"
    io.open(dst, "w", encoding="utf-8", newline="").write(
        SWEEP.read_text(encoding="utf-8"))
    r = subprocess.run(["bash", "-n", str(OUT)], capture_output=True)
    print(f"  bash -n: {'OK' if r.returncode == 0 else r.stderr.decode('utf-8', 'replace')}")
    print(f"  wrote {OUT.name} and {dst.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

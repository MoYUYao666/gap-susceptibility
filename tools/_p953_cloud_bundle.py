# -*- coding: utf-8 -*-
r"""Pack everything the cloud run needs, and pin the environment it must match.

One archive, to be copied to the cloud instance and unpacked there:

    p3_llava_cloud.zip
      tools/_p820_llava_sites.py        the sweep, with --coco-root / --bench-steps / --report-every
      cloud_fixture/                    the exact 700 COCO images and their annotations
      environment.txt                   what to install, version by version
      SETUP.sh                          installs the environment and fetches the model
      PARITY.sh                         the small run whose losses are compared with the local baseline
      RUN_FULL.sh                       the full sweep
      MANIFEST.json                     id order, hashes, and the local loss baseline

The versions are copied from the machine that produced the local baseline, so `SETUP.sh` installs the same
stack rather than "a recent one": torch 2.9.1 built for CUDA 13.0, transformers 5.16.1, peft 0.20.0,
bitsandbytes 0.50.2, accelerate 1.14.0.

    python tools/_p953_cloud_bundle.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY_LOCAL = r"D:\Anaconda\envs\pytorch\python.exe"
OUT = REPO / "cloud_fixture" / "p3_llava_cloud.zip"
SWEEP = REPO / "tools" / "_p820_llava_sites.py"
FIXTURE = REPO / "cloud_fixture"

ENV_SCRIPT = r"""#!/usr/bin/env bash
# Exactly the stack that produced the local baseline (Windows, RTX 4060 Laptop, 2026-10-15).
# Do not "upgrade to latest": a different transformers or bitsandbytes changes the loss.
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install \
  "torch==2.9.1" --index-url https://download.pytorch.org/whl/cu130
python -m pip install \
  "transformers==5.16.1" \
  "peft==0.20.0" \
  "bitsandbytes==0.50.2" \
  "accelerate==1.14.0" \
  "datasets==5.0.1" \
  "pillow==12.3.0" \
  "numpy==2.5.2" \
  "sentencepiece" \
  "protobuf"

python - <<'EOF'
import sys, importlib
want = {"torch": "2.9.1", "transformers": "5.16.1", "peft": "0.20.0",
        "bitsandbytes": "0.50.2", "accelerate": "1.14.0"}
bad = []
for name, ver in want.items():
    got = getattr(importlib.import_module(name), "__version__", "?")
    ok = got.startswith(ver.split("+")[0])
    print(("  OK  " if ok else "  BAD ") + name + " " + got + " (want " + ver + ")")
    if not ok:
        bad.append(name)
if bad:
    sys.exit("version mismatch: " + ", ".join(bad))
import torch
print("  python", sys.version.split()[0], "| cuda", torch.version.cuda,
      "| device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
EOF

# The model is fetched on the server, never uploaded (project rule).
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HUB_DISABLE_XET=1
python -c "from huggingface_hub import snapshot_download; snapshot_download('llava-hf/llava-1.5-7b-hf')"
echo "setup done"
"""

PARITY_SCRIPT = r"""#!/usr/bin/env bash
# The parity run. Its losses are compared against MANIFEST.json -> parity_test loses.
# 20 training pairs, 10 held-out pairs, 25 steps: a few minutes, not hours.
set -euo pipefail
export PYTHONIOENCODING=utf-8
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --bench-steps 25 --report-every 5 --apply \
  --out-dir outputs/llava_parity_cloud 2>&1 | tee parity_cloud.log
echo "--- the losses above must match the local baseline to about 1e-3 ---"
"""

FULL_SCRIPT = r"""#!/usr/bin/env bash
# The full sweep, with the parameters the manuscript quotes. Roughly 14 h per run per GPU on a 4060
# Laptop; on a larger device it is faster. `--report-every 20` prints a heartbeat with an ETA.
set -euo pipefail
export PYTHONIOENCODING=utf-8
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_ALLOC_CONF=expandable_segments:True
python -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture \
  --samples 400 --eval-pairs 300 --epochs 3 --batch 2 --max-len 2048 \
  --seeds 3 --lr 1e-4 --rank 8 \
  --arms frozen,text_only,vision_only,both --apply --report-every 20 \
  --out-dir outputs/llava_sites_cloud 2>&1 | tee full_sweep_cloud.log
"""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    versions = subprocess.run([PY_LOCAL, "-c", "import torch;print(torch.__version__, torch.version.cuda)"],
                              capture_output=True).stdout.decode().strip()
    print(f"  local torch: {versions}")
    files = [(SWEEP, "tools/_p820_llava_sites.py")]
    for p in sorted((FIXTURE / "val2014").glob("*.jpg")):
        files.append((p, "cloud_fixture/val2014/" + p.name))
    files.append((FIXTURE / "annotations" / "captions_val2014.json",
                  "cloud_fixture/annotations/captions_val2014.json"))
    files.append((FIXTURE / "MANIFEST.json", "cloud_fixture/MANIFEST.json"))
    missing = [str(s) for s, _ in files if not s.exists()]
    assert not missing, f"missing {missing}"
    total = sum(s.stat().st_size for s, _ in files)
    print(f"  payload: {len(files)} files, {total / 1e6:.1f} MB uncompressed")

    if not a.apply:
        print("  (dry run)")
        return 0

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for src, arc in files:
            z.write(src, arcname=arc)
        z.writestr("environment.txt", ENV_SCRIPT)
        z.writestr("SETUP.sh", ENV_SCRIPT)
        z.writestr("PARITY.sh", PARITY_SCRIPT)
        z.writestr("RUN_FULL.sh", FULL_SCRIPT)
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        names = z.namelist()
        for src, arc in files:
            assert hashlib.sha256(z.read(arc)).hexdigest() == sha256(src), arc
    print(f"  wrote {OUT.relative_to(REPO).as_posix()}: {OUT.stat().st_size / 1e6:.1f} MB, "
          f"{len(names)} entries, every member byte-identical to its source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

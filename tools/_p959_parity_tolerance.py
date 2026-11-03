# -*- coding: utf-8 -*-
r"""Update the cloud bundle's parity instructions and manifest with the measured tolerance.

The comparison tolerance is not a guess: the local machine, running the same configuration twice, differs
by 1.7e-3 at step 5 (2.9466 vs 2.9449), and adding the determinism switches only brings that to the same
order (2.9496) while costing 4.4x in time. The instructions therefore ask for agreement to **5e-3 per
step**, and note the switches as an option for a tighter check.

Also records the fixture's remaining caveat: the checkpoint files are not shipped, so a cloud run restarts
from a fresh LoRA initialisation, which is what the local baseline also did.

    python tools/_p959_parity_tolerance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "cloud_fixture" / "MANIFEST.json"
ZIP = REPO / "cloud_fixture" / "p3_llava_cloud.zip"
PARITY = "PARITY.sh"

PARITY_NEW = r"""#!/usr/bin/env bash
# Parity run: 20 training pairs, 10 held-out pairs, batch 2, seed 42, five steps.
# Compare its losses against cloud_fixture/MANIFEST.json -> parity_baseline.losses_at_step.
#
# Tolerance: 5e-3 per step. This is measured, not assumed -- the machine that produced the baseline
# differs from itself by 1.7e-3 between runs at step 5 (2.9466 vs 2.9449), because cuDNN picks its
# convolution algorithm afresh and 4-bit kernels vary. Add --deterministic below for a tighter check at
# 4.4x the time (measured 63 -> 279 s per step); it is not used for the sweep for that reason.
set -euo pipefail
export PYTHONIOENCODING=utf-8
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python -u -X utf8 tools/_p820_llava_sites.py \
  --coco-root cloud_fixture \
  --samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 \
  --seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply \
  --out-dir outputs/llava_parity_cloud 2>&1 | tee parity_cloud.log
echo "--- compare the step-5 loss above with the baseline in cloud_fixture/MANIFEST.json (tolerance 5e-3) ---"
"""

TOLERANCE_NOTE = (
    "Tolerance 5e-3 per step, measured rather than assumed: the local machine differs from itself by "
    "1.7e-3 at step 5 between runs. The `--deterministic` flag tightens this but costs 4.4x in time "
    "(63 -> 279 s per step), so it is reserved for parity runs and never used for the sweep. If the cloud "
    "disagrees by more than 5e-3, stop and check in this order: (1) id_order_sha256, (2) the number and "
    "hashes of the images, (3) the package versions printed by SETUP.sh, (4) the model revision."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man["parity_baseline"]["tolerance_per_step"] = 5e-3
    man["parity_baseline"]["tolerance_note"] = TOLERANCE_NOTE
    man["parity_baseline"]["determinism"] = {
        "default": "off",
        "flag": "--deterministic",
        "measured_spread_without": {"loss_at_step_5": [2.9466, 2.9449], "difference": 0.0017},
        "measured_spread_with": {"loss_at_step_5": 2.9496},
        "cost_with_flag_s_per_step": 278.9,
        "cost_without_flag_s_per_step": 63.3,
    }
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(man, indent=1))
    print("  manifest: tolerance 5e-3 and the determinism measurements recorded")

    # repack, replacing PARITY.sh with the annotated version
    tmp = ZIP.with_suffix(".tmp")
    with zipfile.ZipFile(ZIP) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED,
                                                     compresslevel=6) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == PARITY:
                data = PARITY_NEW.encode("utf-8")
            elif item.filename == "cloud_fixture/MANIFEST.json":
                data = MANIFEST.read_bytes()
            elif item.filename == "tools/_p820_llava_sites.py":
                data = (REPO / "tools" / "_p820_llava_sites.py").read_bytes()
            dst.writestr(item.filename, data)
    tmp.replace(ZIP)
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        man_in = json.loads(z.read("cloud_fixture/MANIFEST.json"))
        assert man_in["parity_baseline"]["tolerance_per_step"] == 5e-3
        assert b"--deterministic" in z.read(PARITY)
        sweep = z.read("tools/_p820_llava_sites.py").decode("utf-8")
        assert "a.deterministic" in sweep, "the bundled sweep is not the flagged version"
    print(f"  repacked {ZIP.name}: {ZIP.stat().st_size / 1e6:.1f} MB, "
          f"with the annotated PARITY.sh, the current sweep and the updated manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())

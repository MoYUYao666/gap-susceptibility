# -*- coding: utf-8 -*-
r"""Put the completed local parity baseline into the cloud fixture's manifest and repack the bundle.

The cloud cannot be judged "correct" without the reference numbers, so the manifest carries them:

* the exact command,
* the token geometry of the first batch,
* the loss at each heartbeat,
* the per-step time, so the cloud's timing can be sanity-checked even though it will differ by hardware.

    python tools/_p955_parity_baseline.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "outputs" / "analysis" / "_p952_parity_local.log"
MANIFEST = REPO / "cloud_fixture" / "MANIFEST.json"
CMD = ("python tools/_p820_llava_sites.py --coco-root cloud_fixture "
       "--samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 "
       "--seeds 1 --rank 8 --bench-steps 25 --report-every 5 --apply "
       "--out-dir outputs/llava_parity_cloud")


def read_log(p: Path) -> str:
    raw = p.read_bytes()
    t = raw.decode("utf-16-le", "replace") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else \
        raw.decode("utf-8", "replace")
    return t.replace("\x00", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    txt = read_log(LOG)
    beats = re.findall(r"step (\d+)/\d+\s+loss ([\d.]+)\s+([\d.]+) s/step", txt)
    toks = re.findall(r"batch tokens:\s+(\d+) mean (\d+)", txt)
    ep = re.findall(r"epoch 1/1\s+loss ([\d.]+)\s+\[([\d.]+) min, (\d+) steps, ([\d.]+) s/step\]", txt)
    meas = re.findall(r"held-out measurement: ([\d.]+) s over (\d+) pairs", txt)
    base = {
        "command": CMD,
        "note": ("Ran on the local machine on 2026-10-15. The cloud run of the same command must "
                 "reproduce these losses to about 1e-3; the per-step time will differ with the device."),
        "device": "NVIDIA GeForce RTX 4060 Laptop GPU, 8.6 GB, 4-bit nf4",
        "first_batch": {"tokens": int(toks[0][0]) if toks else None,
                        "mean_per_sequence": int(toks[0][1]) if toks else None},
        "losses_at_step": {int(s): float(l) for s, l, _t in beats},
        "sec_per_step": float(beats[-1][2]) if beats else None,
        "epoch_summary": ({"final_loss": float(ep[0][0]), "minutes": float(ep[0][1]),
                           "steps": int(ep[0][2]), "sec_per_step": float(ep[0][3])} if ep else None),
        "held_out_measurement": ({"seconds": float(meas[-1][0]), "pairs": int(meas[-1][1])}
                                 if meas else None),
    }
    print(f"  losses at step: {base['losses_at_step']}")
    print(f"  first batch: {base['first_batch']}, {base['sec_per_step']} s/step")

    if not a.apply:
        print("  (dry run)")
        return 0

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man["parity_baseline"] = base
    man["parity_test"] = (
        "Run PARITY.sh on the cloud, then compare its heartbeat losses with parity_baseline."
        "losses_at_step. They must agree to about 1e-3. If they do not, stop and check, in this order: "
        "(1) id_order_sha256, (2) the number and hashes of the images, (3) the package versions printed "
        "by SETUP.sh, (4) that the same model revision was fetched."
    )
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(man, indent=1))
    print(f"  manifest updated with the baseline")

    r = subprocess.run([sys.executable, str(REPO / "tools" / "_p953_cloud_bundle.py"), "--apply"],
                       cwd=REPO, capture_output=True)
    out = (r.stdout.decode("utf-8", "replace").strip().splitlines() or ["(no output)"])[-1]
    print("  bundle: " + out)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

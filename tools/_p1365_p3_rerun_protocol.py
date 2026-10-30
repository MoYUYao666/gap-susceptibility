# -*- coding: utf-8 -*-
r"""P3: re-run the rank family under the *current* training script to pin down the reproducible critical rank.

The archived E2 family and the dense sweep were produced by older versions of run_training.py (their E0 values 3927.0 /
3930.5 are not produced by the current script, which gives E0 = 3921.0 for the same rank/seed). This runner executes the
current script for ranks 5, 6 and 16 at seed 42 for three epochs and records the E trajectories, so the crossing can be
stated for the current, reproducible protocol.

Output: outputs/analysis/p3_rerun_protocol.json ; log outputs/analysis/_p1365_rerun.log

    conda run -n pytorch python tools/_p1365_p3_rerun_protocol.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_rerun_protocol.json")
LOG = os.path.join(REPO, "outputs", "analysis", "_p1365_rerun.log")
RANKS = [5, 6, 16]
SEED = 42
EPOCHS = 3


def main() -> int:
    env = dict(os.environ)
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    payload = {"protocol": "current paper3/scripts/run_training.py defaults: num_samples=20 (16 train / 4 eval), "
                          "lr=5e-5, attn_targets=qkvo, float16, batch_size=1, blank-image protocol",
               "script": "paper3/scripts/run_training.py", "seed": SEED, "epochs": EPOCHS, "runs": {}}
    logf = io.open(LOG, "w", encoding="utf-8")
    for rank in RANKS:
        t0 = time.time()
        cmd = [sys.executable, SCRIPT, "--rank", str(rank), "--seed", str(SEED), "--epochs", str(EPOCHS)]
        logf.write("\n==== %s\n" % " ".join(cmd))
        logf.flush()
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=5400)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        logf.write(out)
        logf.flush()
        es = [(int(m.group(1)), float(m.group(2))) for m in re.finditer(r"E\((\d+)\)\s*=\s*([0-9.]+)", out)]
        es = [v for _, v in sorted(es)]
        ok = r.returncode == 0 and len(es) >= 2 and es[-1] == es[-1]
        entry = {"rank": rank, "seed": SEED, "epochs": EPOCHS, "E": es, "ok": ok,
                 "delta_E": (es[-1] - es[0]) if ok else None,
                 "elapsed_min": round((time.time() - t0) / 60, 1), "returncode": r.returncode}
        payload["runs"][f"r{rank}_s{SEED}"] = entry
        print(f"  rank {rank}: E={es} ΔE={entry['delta_E']} ok={ok} ({entry['elapsed_min']} min)", flush=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    logf.close()
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

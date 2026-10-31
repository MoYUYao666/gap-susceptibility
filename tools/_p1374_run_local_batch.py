# -*- coding: utf-8 -*-
r"""Run the local upgrade batch sequentially on the local GPU (no cloud).

Order (each step writes its own archive):
  1. A1 early-stopping baselines + third dataset      (_p1369)
  2. A23 order-preservation (tau) positive control     (_p1370)
  3. A1 per-epoch checkpoint hook                      (_p1373)
  4. Qwen2-VL-2B local crossing check                  (_p1372)
  5. P3 extra ranks / second seed                      (_p1371)

A failing step is recorded and the batch continues. Log: outputs/_log_local_batch.log

    conda run -n pytorch python tools/_p1374_run_local_batch.py
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, "outputs", "_log_local_batch.log")
JOBS = [
    ("a1_stopping_baselines", ["tools/_p1369_a1_stopping_baselines.py", "--apply"]),
    ("a23_tau_control", ["tools/_p1370_a23_tau_control.py", "--apply"]),
    ("a1_ckpt_hook", ["tools/_p1373_a1_ckpt_hook.py", "--apply"]),
    ("qwen2b_crossing", ["tools/_p1372_qwen2b_crossing.py"]),
    ("p3_extra_ranks", ["tools/_p1371_p3_extra_ranks.py"]),
]


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    logf = io.open(LOG, "w", encoding="utf-8")
    for name, argv in JOBS:
        t0 = time.time()
        cmd = [sys.executable] + argv
        logf.write("\n\n######## %s | %s\n" % (name, " ".join(cmd)))
        logf.flush()
        print("===", name, flush=True)
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=4 * 3600)
        logf.write((r.stdout or "") + "\n" + (r.stderr or ""))
        logf.write("\n#### %s exit=%s elapsed=%.1f min\n" % (name, r.returncode, (time.time() - t0) / 60))
        logf.flush()
        print(f"   {name} exit={r.returncode} ({round((time.time()-t0)/60,1)} min)", flush=True)
    logf.close()
    print("  batch done; log:", os.path.relpath(LOG, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

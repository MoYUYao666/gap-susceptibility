# -*- coding: utf-8 -*-
r"""Run the Round-1 and Round-2 local upgrade batch sequentially on the local GPU.

Order:
  1. A1 train-split margin monitor    (_p1410)
  2. A1 both-tower LoRA monitor       (_p1411)
  3. A1 retrieval monitor             (_p1412)
  4. A23 water-tank acoustic corpus   (_p1414)
  5. A23 n_eval sensitivity           (_p1415)
  6. P3 extra seeds                   (_p1416)
  7. P3 num-samples ablation          (_p1417)

Log: outputs/_log_rounds_batch.log

    conda run -n pytorch python tools/_p1418_run_rounds.py
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, "outputs", "_log_rounds_batch.log")
JOBS = [
    ("a1_trainmass", ["tools/_p1410_a1_trainmass.py", "--apply"]),
    ("a1_bothtower", ["tools/_p1411_a1_bothtower.py", "--apply"]),
    ("a1_retrieval", ["tools/_p1412_a1_retrieval_monitor.py", "--apply"]),
    ("a23_watertank", ["tools/_p1414_a23_watertank.py", "--apply"]),
    ("a23_neval", ["tools/_p1415_a23_neval.py", "--apply"]),
    ("p3_seeds", ["tools/_p1416_p3_seeds.py"]),
    ("p3_numsamples", ["tools/_p1417_p3_numsamples.py"]),
]


def main() -> int:
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    logf = io.open(LOG, "w", encoding="utf-8")
    for name, argv in JOBS:
        t0 = time.time()
        logf.write("\n\n######## %s | %s\n" % (name, " ".join(argv)))
        logf.flush()
        print("===", name, flush=True)
        r = subprocess.run([sys.executable] + argv, cwd=REPO, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=6 * 3600)
        logf.write((r.stdout or "") + "\n" + (r.stderr or ""))
        logf.write("\n#### %s exit=%s elapsed=%.1f min\n" % (name, r.returncode, (time.time() - t0) / 60))
        logf.flush()
        print(f"   {name} exit={r.returncode} ({round((time.time()-t0)/60,1)} min)", flush=True)
    logf.close()
    print("  batch done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

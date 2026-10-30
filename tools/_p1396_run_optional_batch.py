# -*- coding: utf-8 -*-
r"""Run the optional local batch: corrected Qwen2-VL-2B check, extra A1 monitoring seeds/domain, tau calibration.

Sequential on the local GPU; log outputs/_log_optional_batch.log.

    conda run -n pytorch python tools/_p1396_run_optional_batch.py
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, "outputs", "_log_optional_batch.log")
JOBS = [
    ("qwen2b_fixed", ["tools/_p1391_qwen2b_fixed.py"]),
    ("a1_monitor_extra", ["tools/_p1392_a1_monitor_extra.py", "--apply"]),
    ("a23_tau_calibration", ["tools/_p1393_a23_tau_calibration.py", "--apply"]),
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
                           encoding="utf-8", errors="replace", timeout=4 * 3600)
        logf.write((r.stdout or "") + "\n" + (r.stderr or ""))
        logf.write("\n#### %s exit=%s elapsed=%.1f min\n" % (name, r.returncode, (time.time() - t0) / 60))
        logf.flush()
        print(f"   {name} exit={r.returncode} ({round((time.time()-t0)/60,1)} min)", flush=True)
    logf.close()
    print("  batch done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

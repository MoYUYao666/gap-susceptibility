# -*- coding: utf-8 -*-
r"""Wait for the P3 extra-rank batch, then run the queued local jobs (UATD domain, P3 analysis).

Runs in the background; writes outputs/_log_after_p3.log.

    conda run -n pytorch python tools/_p1383_wait_then_after.py
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA = os.path.join(REPO, "outputs", "analysis", "p3_rerun_extra.json")
LOG = os.path.join(REPO, "outputs", "_log_after_p3.log")
EXPECTED = {"r7_s42", "r8_s42", "r10_s42", "r5_s123", "r6_s123"}
MAX_WAIT = 4 * 3600


def ready() -> bool:
    if not os.path.exists(EXTRA):
        return False
    d = json.load(io.open(EXTRA, encoding="utf-8"))
    return EXPECTED.issubset({k for k, v in d.get("runs", {}).items() if v.get("ok")})


def main() -> int:
    logf = io.open(LOG, "w", encoding="utf-8")
    t0 = time.time()
    while time.time() - t0 < MAX_WAIT:
        if ready():
            break
        time.sleep(60)
    ok = ready()
    logf.write("ready=%s after %.1f min\n" % (ok, (time.time() - t0) / 60))
    logf.flush()
    env = dict(os.environ)
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    for argv in (["tools/_p1382_a23_uatd_domain.py", "--apply"], ["tools/_p1378_p3_extra_analysis.py", "--apply"]):
        logf.write("\n#### %s\n" % " ".join(argv))
        logf.flush()
        r = subprocess.run([sys.executable] + argv, cwd=REPO, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
        logf.write((r.stdout or "") + "\n" + (r.stderr or ""))
        logf.write("\n#### exit=%s\n" % r.returncode)
        logf.flush()
    logf.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

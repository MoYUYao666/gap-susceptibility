# -*- coding: utf-8 -*-
r"""Follow-up GPU batch: after the P3 seed/ablation runs finish, run the A1 both-tower LoRA monitoring.

Polls the P3 result files, then runs tools/_p1411_a1_bothtower.py --apply (the only GPU job left in Round 1/2) and reports
where it wrote its archive.

    python tools/_p1451_after_p3.py
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(REPO, "outputs", "analysis", "p3_rerun_seeds.json")
ABL = os.path.join(REPO, "outputs", "analysis", "p3_numsamples_ablation.json")
OUT = os.path.join(REPO, "outputs", "analysis", "a1_monitor_bothtower.json")


def n_ok(path):
    if not os.path.exists(path):
        return 0
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return 0
    return sum(1 for v in d.get("runs", {}).values() if v.get("ok"))


def main() -> int:
    t0 = time.time()
    while time.time() - t0 < 9 * 3600:
        if n_ok(SEEDS) >= 6 and n_ok(ABL) >= 3:
            break
        time.sleep(60)
    else:
        print("  timeout waiting for the P3 batch")
        return 1
    print("  P3 batch complete; starting the A1 both-tower run", flush=True)
    r = subprocess.run([sys.executable, "tools/_p1411_a1_bothtower.py", "--apply"], cwd=REPO,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    print((r.stdout or "")[-2000:])
    print("exit", r.returncode, "archive", os.path.relpath(OUT, REPO) if os.path.exists(OUT) else "missing")
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

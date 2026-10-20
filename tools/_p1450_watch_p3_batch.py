# -*- coding: utf-8 -*-
r"""Watch the P3 Round-2 batch and exit when all seed and ablation runs are complete.

Polls the two result JSONs every 60 s and prints a progress line every 5 min; exits 0 when the expected number of runs is
recorded, or 1 after the timeout.

    python tools/_p1450_watch_p3_batch.py --seeds 6 --ablation 2
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(REPO, "outputs", "analysis", "p3_rerun_seeds.json")
ABL = os.path.join(REPO, "outputs", "analysis", "p3_numsamples_ablation.json")


def ok_count(path, key="runs"):
    if not os.path.exists(path):
        return {}
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return {}
    return {k: v.get("delta_E") for k, v in d.get(key, {}).items() if v.get("ok")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--ablation", type=int, default=2)
    ap.add_argument("--timeout-hours", type=float, default=7.0)
    a = ap.parse_args()
    t0 = time.time()
    last = 0.0
    while time.time() - t0 < a.timeout_hours * 3600:
        s = ok_count(SEEDS)
        ab = ok_count(ABL)
        now = time.time()
        if now - last > 300:
            print("  [%s] seeds %d/%d %s | ablation %d/%d %s" % (
                time.strftime("%H:%M:%S"), len(s), a.seeds,
                {k: round(v, 1) for k, v in s.items()}, len(ab), a.ablation,
                {k: round(v, 1) for k, v in ab.items()}), flush=True)
            last = now
        if len(s) >= a.seeds and len(ab) >= a.ablation:
            print("  DONE seeds=%s ablation=%s" % (
                {k: round(v, 1) for k, v in s.items()}, {k: round(v, 1) for k, v in ab.items()}), flush=True)
            return 0
        time.sleep(60)
    print("  TIMEOUT after %.1f h: seeds=%d ablation=%d" % (a.timeout_hours, len(ok_count(SEEDS)), len(ok_count(ABL))))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

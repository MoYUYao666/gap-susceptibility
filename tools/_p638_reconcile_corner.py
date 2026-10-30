# -*- coding: utf-8 -*-
r"""Reconcile the corner configuration: the paper says +3607 +- 514, the archive says 2343.9.

Two possibilities: (a) the paper quotes a different experiment (a different corner
definition or a different arm), or (b) one of the two is wrong. This reads the per-run
records, recomputes the mean, and searches the archive for anything that produces 3607.

    python tools/_p638_reconcile_corner.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "corner_reconcile.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 96)
    print("1. per-run records for each plan in the allocation study")
    print("=" * 96)
    base = REPO / "outputs" / "analysis" / "p3_alloc_runs" / "main"
    if not base.exists():
        base = REPO / "publish_clean" / "outputs" / "analysis" / "p3_alloc_runs" / "main"
    plans: dict[str, list[tuple[str, float, dict]]] = {}
    for p in sorted(base.glob("*.json")):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        except Exception as e:
            print(f"  cannot read {p.name}: {e}")
            continue
        plan = p.name.split("__")[0]
        # find the delta E field
        de = None
        for k in ("delta_E", "deltaE", "dE", "delta_e"):
            if k in d:
                de = d[k]
                break
        if de is None:
            for k, v in d.items():
                if isinstance(v, (int, float)) and "delta" in k.lower():
                    de = v
                    break
        if de is None:
            continue
        plans.setdefault(plan, []).append((p.name, float(de), d))
    for plan, rows in sorted(plans.items()):
        vals = [v for _, v, _ in rows]
        print(f"  {plan:<34} n={len(vals):<3} mean={statistics.mean(vals):>10.2f}  "
              f"sd={statistics.stdev(vals) if len(vals) > 1 else 0:>9.2f}  "
              f"seeds={[r[0].split('seed')[-1].replace('.json','') for r in rows]}")
    print()
    print("  Plans present:", sorted(plans))

    print()
    print("=" * 96)
    print("2. where does 3607 come from?")
    print("=" * 96)
    r = subprocess.run(["git", "grep", "-n", "-F", "3607", "--", "."],
                       cwd=str(REPO), capture_output=True)
    for line in r.stdout.decode("utf-8", errors="replace").splitlines()[:20]:
        print("  " + line[:150])
    print()
    r = subprocess.run(["git", "grep", "-n", "-F", "514", "--", "outputs/", "tools/"],
                       cwd=str(REPO), capture_output=True)
    hits = [l for l in r.stdout.decode("utf-8", errors="replace").splitlines()
            if "3607" in l or "514" in l][:15]
    for line in hits:
        print("  " + line[:150])

    print()
    print("=" * 96)
    print("3. the sentence in the paper")
    print("=" * 96)
    t = io.open(REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex",
                encoding="utf-8", errors="replace").read()
    i = t.find("capacity-matched corner")
    if i > 0:
        print("  " + " ".join(t[max(0, i - 320):i + 420].split()))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {p: {"n": len(v), "mean": statistics.mean([x for _, x, _ in v]),
                 "sd": statistics.stdev([x for _, x, _ in v]) if len(v) > 1 else 0,
                 "files": [f for f, _, _ in v]} for p, v in plans.items()},
            ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

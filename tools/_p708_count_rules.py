# -*- coding: utf-8 -*-
r"""Try to source the count-type GAPs by counting the archive, with an explicit rule each.

Paper A states several counts: 383 experiments in the validation part, 221 runs in the catalogue,
117 mechanism experiments, 95 strict-freezing controls, 222 fits archived, 203 with negative
alpha, and an OpenCLIP BitFit R2 of 0.943. The ledger found no stored field for them.

Counts can be re-sourced by defining a counting rule over the tracked archive. This tries
plausible rule definitions from the families that exist, and reports the closest match to the
paper's number with the exact rule that produces it. If no rule lands on the number, that is the
honest answer and the number must be re-examined.

    python tools/_p708_count_rules.py [--apply]
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
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "paperhe_count_rules.json"

TARGETS = {"383": "experiments in the validation part",
           "221": "runs in the experiment catalogue",
           "117": "mechanism experiments",
           "95": "strict-freezing controls",
           "222": "fits archived",
           "203": "fits with negative alpha"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    print(f"  {len(files)} tracked files under outputs/")
    print()

    # candidate counting rules over tracked paths
    rules = {
        "per-run results.json anywhere": lambda f: f.endswith("results.json"),
        "per-run gap_history.json anywhere": lambda f: f.endswith("gap_history.json"),
        "results.json or eval_epoch*.json": lambda f: (
            f.endswith("results.json") or "eval_epoch" in f),
        "under strict_freeze*": lambda f: "strict_freeze" in f and f.endswith(".json"),
        "under theory/": lambda f: f.startswith("outputs/theory/") and f.endswith(".json"),
        "under coco_sweep*": lambda f: "coco_sweep" in f and f.endswith(".json"),
        "under outputs/a1_class_aligned/": lambda f: (
            f.startswith("outputs/a1_class_aligned/") and f.endswith(".json")),
        "any json under outputs/analysis/": lambda f: (
            f.startswith("outputs/analysis/") and f.endswith(".json")),
        "any json under outputs/": lambda f: f.endswith(".json"),
        "svg/png figures": lambda f: f.endswith((".png", ".pdf", ".svg")),
    }
    counts = {label: sum(1 for f in files if pred(f)) for label, pred in rules.items()}
    print("=" * 104)
    print("candidate counts")
    print("=" * 104)
    for label, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>6}  {label}")

    print()
    print("=" * 104)
    print("which rule, if any, lands on each number in the paper")
    print("=" * 104)
    result = {}
    for target, desc in TARGETS.items():
        t = int(target)
        exact = [label for label, n in counts.items() if n == t]
        close = [(label, n) for label, n in counts.items() if abs(n - t) <= max(3, t * 0.03)]
        print(f"  {target:<6} {desc}")
        if exact:
            print(f"        EXACT match with rule: {exact}")
        elif close:
            print(f"        no exact rule; closest: {close}")
        else:
            print(f"        no rule within 3%; nearest is "
                  f"{min(counts.items(), key=lambda kv: abs(kv[1] - t))}")
        result[target] = {"exact_rules": exact,
                          "close": [{"rule": l, "count": n} for l, n in close]}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"counts": counts, "per_target": result}, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

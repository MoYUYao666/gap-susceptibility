# -*- coding: utf-8 -*-
r"""List which ranks the archive's Flickr30k LoRA runs cover, so the rerun can match them.

Paper A's ODE fit (mean R^2 = 0.949 over 55 runs) uses trajectories from those runs, and they came
from the defective adapter path. Before rerunning anything this establishes the rank grid actually
used, so the rerun covers the same one.

    python tools/_p811_flickr_grid.py
"""
from __future__ import annotations

import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    r = subprocess.run(["git", "ls-files", "outputs/theory"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", "replace").splitlines()
             if x.endswith("results.json")]
    ranks = Counter()
    fams = Counter()
    for f in files:
        p = PUB / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        exp = str(d.get("experiment", ""))
        n = d.get("n_trainable_params")
        m = re.search(r"r(\d+)", exp)
        parts = f.split("/")
        fam = parts[2] if len(parts) > 2 else parts[1]
        if m:
            ranks[int(m.group(1))] += 1
        fams[fam] += 1
    print("  ranks seen in outputs/theory run names:")
    for k in sorted(ranks):
        print(f"     r{k:<4} {ranks[k]} run(s)")
    print()
    print("  families:")
    for k, v in fams.most_common():
        print(f"     {k:<24} {v}")
    print()
    # which files hold the trajectory used for the ODE fit
    hist = [f for f in files if f.endswith("results.json")]
    seen = set()
    for f in hist:
        p = PUB / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        exp = str(d.get("experiment", ""))
        if exp and exp not in seen:
            seen.add(exp)
    print(f"  distinct experiment names: {len(seen)}")
    print(f"  examples: {sorted(seen)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""Locate the source of Paper A's "222 fits archived, 203 with negative alpha".

The paper states: "Across the 222 fits we archived, alpha < 0 in 203; the 19 exceptions are ten of
the fifty Adapter fits (largest +0.061), four LoRA fits (largest +0.011) and all three CLIP BitFit
fits". Those exception counts are specific enough to identify the population: 50 Adapter fits,
some LoRA fits, 3 CLIP BitFit fits, 222 in total.

This searches for the file that holds that population.

    python tools/_p712_find_fit_population.py [--apply]
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

POPULATION_HINTS = ["ode", "fit", "loco", "alpha", "theory"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 112)
    print("1. candidate files whose name suggests a population of ODE fits")
    print("=" * 112)
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    cands = [f for f in files
             if any(h in f.lower() for h in POPULATION_HINTS) and f.endswith(".json")]
    for f in cands:
        p = PUB / f
        print(f"  {p.stat().st_size:>10,}  {f}")
    print(f"  ... {len(cands)} candidates")

    print()
    print("=" * 112)
    print("2. which of them, when read, contains 222 fits with 50 adapter entries")
    print("=" * 112)
    for f in cands:
        p = PUB / f
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        # look for a list of dicts carrying alpha and a family-ish key
        def lists_of_dicts(o, path="$"):
            if isinstance(o, list) and o and isinstance(o[0], dict):
                yield path, o
            if isinstance(o, dict):
                for k, v in o.items():
                    yield from lists_of_dicts(v, f"{path}.{k}")
        for path, lst in lists_of_dicts(d):
            keys = set(lst[0].keys())
            if not ({"alpha"} & keys or {"r_squared", "R2"} & keys):
                continue
            n = len(lst)
            fams = {}
            for e in lst:
                fam = str(e.get("family") or e.get("method") or e.get("tag") or "?")
                fams[fam] = fams.get(fam, 0) + 1
            neg = sum(1 for e in lst
                      if isinstance(e.get("alpha"), (int, float)) and e["alpha"] < 0)
            flag = "  <<< MATCHES 222" if n == 222 else ""
            print(f"  {f}")
            print(f"     {path}: {n} entries, alpha<0 = {neg}, families {fams}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

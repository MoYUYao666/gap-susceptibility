# -*- coding: utf-8 -*-
r"""Read the alpha sign audit in full, and try to reproduce Paper A's 222 / 203.

Paper A says: "Across the 222 fits we archived, alpha < 0 in 203; the 19 exceptions are ten of the
fifty Adapter fits (largest +0.061), four LoRA fits (largest +0.011) and all three CLIP BitFit
fits".

outputs/analysis/alpha_sign_audit.json audits the alpha sign of several archive files. If the
paper's population is their sum, the ledger can assert on it. This prints the whole audit and the
totals.

    python tools/_p713_alpha_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p = PUB / "outputs/analysis/alpha_sign_audit.json"
    d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    print("=" * 112)
    print("alpha_sign_audit.json")
    print("=" * 112)
    tot_n = tot_neg = 0
    for k, v in d.items():
        if not isinstance(v, dict) or "n" not in v:
            print(f"  {k}: {v if not isinstance(v, dict) else list(v.keys())}")
            continue
        print(f"  {k}")
        print(f"     n = {v['n']}  neg = {v['neg']}  nonneg = {v['nonneg']}  "
              f"min = {v.get('min')}  max = {v.get('max')}")
        tot_n += v["n"]
        tot_neg += v["neg"]
    print()
    print(f"  SUM over audited files: n = {tot_n}, negative = {tot_neg}, "
          f"non-negative = {tot_n - tot_neg}")
    print(f"  Paper A states        : n = 222, negative = 203, exceptions = 19")
    print(f"  match: n {tot_n == 222}, negative {tot_neg == 203}")

    print()
    print("=" * 112)
    print("for comparison, the current contents of the audited files")
    print("=" * 112)
    for k in d:
        q = PUB / k
        if not q.exists():
            print(f"  {k}: no longer present")
            continue
        try:
            o = json.loads(q.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            print(f"  {k}: unreadable ({str(e)[:40]})")
            continue
        if isinstance(o, list):
            print(f"  {k}: list[{len(o)}]")
        elif isinstance(o, dict):
            runs = o.get("runs")
            per = o.get("per_config")
            print(f"  {k}: dict, keys={list(o.keys())[:8]}"
                  + (f", runs={len(runs)}" if isinstance(runs, list) else "")
                  + (f", per_config={len(per)}" if isinstance(per, dict) else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

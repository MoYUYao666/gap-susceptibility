# -*- coding: utf-8 -*-
r"""Decide whether the held-out validation the reviewers asked for should be reported, and how.

R1-W2, R3-2 and AE all demand held-out or out-of-sample validation of the DG-retrieval
association, and the paper currently reports only cluster-robust inference, a clustered bootstrap
and a mixed model. The archive also holds outputs/analysis/pr_stats_hardened.json :: holdout,
which appears to contain leave-one-X-out folds with out-of-sample R2.

This prints those figures and compares them with what the paper claims, so an honest statement can
be added - or the gap declared.

    python tools/_p743_holdout.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "holdout_report.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads((PUB / "outputs/analysis/pr_stats_hardened.json").read_text(
        encoding="utf-8", errors="ignore"))
    ho = d.get("holdout") or {}
    print("=" * 108)
    print("pr_stats_hardened.json :: holdout")
    print("=" * 108)
    print(f"  keys: {list(ho.keys())}")
    for scheme, v in ho.items():
        if not isinstance(v, dict):
            print(f"  {scheme}: {v}")
            continue
        folds = v.get("folds") or []
        print()
        print(f"  {scheme}")
        print(f"     summary keys: {[k for k in v if k != 'folds']}")
        for k in v:
            if k != "folds" and isinstance(v[k], (int, float, str)):
                print(f"        {k} = {v[k]}")
        if folds:
            print(f"     {len(folds)} folds; fold keys {list(folds[0].keys())}")

    print()
    print("=" * 108)
    print("the verdict block's own out-of-sample figures")
    print("=" * 108)
    v = d.get("verdict") or {}
    for k in ("oos_r2_cell", "oos_r2_family", "oos_r2_cell_median_fold",
              "oos_r2_family_median_fold", "oos_frac_folds_beating_baseline_cell",
              "oos_frac_folds_beating_baseline_family", "effective_n_cell", "effective_n_family"):
        print(f"  {k} = {v.get(k)}")

    print()
    print("=" * 108)
    print("what the paper currently says about prediction")
    print("=" * 108)
    for name, t in [("main_nc.tex", io.open(PA / "main_nc.tex", encoding="utf-8",
                                            errors="replace").read())] + \
                   [(p.name, io.open(p, encoding="utf-8", errors="replace").read())
                    for p in sorted((PA / "sections").glob("*.tex"))]:
        for m in re.finditer(r"[^.]*\b(?:predict\w*|association|not a prediction|"
                             r"pre[ck]dictive)\b[^.]*\.", t):
            seg = " ".join(m.group(0).split())
            if re.search(r"association|predict", seg, re.I) and len(seg) > 60:
                ln = t[:m.start()].count("\n") + 1
                print(f"  {name}:{ln}")
                print(f"     {seg[:280]}")
                print()

    stats = {"oos_r2_cell": v.get("oos_r2_cell"), "oos_r2_family": v.get("oos_r2_family"),
             "frac_cell": v.get("oos_frac_folds_beating_baseline_cell"),
             "frac_family": v.get("oos_frac_folds_beating_baseline_family")}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(stats, ensure_ascii=False, indent=1))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

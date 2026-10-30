# -*- coding: utf-8 -*-
r"""Fit the ODE to every available DG* trajectory in the repository, not only those under outputs/theory.

`tools/_p1_ledger.py` globs `outputs/theory/**/dg_star_history.json`, which finds 96 files. The repository actually
holds 127 trajectories under `outputs/`, i.e. **31 complete series were never fitted** -- they sit in
`outputs/coco_sweep_dgstar/`, `outputs/rank_rerun/` and similar directories.

This script reuses the exact fitting routine from `_p1_ledger.py` (same model, same grid, same R^2, same >=5-epoch
rule) so the two ledgers are comparable, and reports:
  * the per-run records for all available trajectories;
  * how the aggregate numbers move relative to the current 96-run ledger;
  * how the manuscript's claimed 162 compares with what is actually reproducible.

    python tools/_p1176_ode_fit_all.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import glob
import importlib.util
import io
import json
import os
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "outputs" / "analysis" / "ode_ledger_all.json"
OLD = REPO / "outputs" / "analysis" / "ode_ledger.json"
FITTER = REPO / "tools" / "_p1_ledger.py"


def load_fitter():
    spec = importlib.util.spec_from_file_location("p1ledger", str(FITTER))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    f = load_fitter()
    print("  fitting routine imported from _p1_ledger.py (same model, grid and R^2)")

    runs = []
    seen = collections.Counter()
    skipped_short = 0
    origins = collections.Counter()
    for p in sorted(glob.glob(str(REPO / "outputs" / "**" / "dg_star_history.json"), recursive=True)):
        rel = Path(p).relative_to(REPO / "outputs")
        try:
            d = json.loads(io.open(p, encoding="utf-8").read())
        except Exception:
            continue
        if len(d.get("epochs", [])) < 5:
            skipped_short += 1
            continue
        A, B, R = f.grid_fit(d["epochs"], d["dg_star"])
        conf = "/".join(rel.parts[:-2])
        meta = f.classify(conf)
        origin = rel.parts[0] if len(rel.parts) > 1 else "."
        origins[origin] += 1
        runs.append(dict(conf=conf, top=origin, seed=rel.parts[-2], n_epoch=len(d["epochs"]),
                         alpha=A, beta=B, R2=R, **meta))
        seen[conf] += 1

    print(f"  trajectories found: {len(runs)} (+{skipped_short} skipped with <5 epochs)")
    print(f"  by top-level directory: {dict(origins)}")
    print(f"  distinct configs: {len(seen)}, configs with >1 seed: {sum(1 for c, n in seen.items() if n > 1)}")

    old = json.loads(io.open(OLD, encoding="utf-8").read()) if OLD.exists() else {}
    old_n = old.get("n_runs_total")
    print(f"\n  current ledger (outputs/theory only): n={old_n}")

    def agg(sel):
        rs = [r["R2"] for r in runs if sel(r) and r["R2"] == r["R2"]]
        if not rs:
            return {"n": 0}
        return {"n": len(rs), "mean": st.mean(rs), "sd": st.pstdev(rs), "median": st.median(rs),
                "min": min(rs), "max": max(rs)}

    subsets = {
        "all": agg(lambda r: True),
        "lora": agg(lambda r: r["family"] == "lora"),
        "lora_flickr": agg(lambda r: r["family"] == "lora" and "flickr" in r["conf"].lower()),
        "lora_coco": agg(lambda r: r["family"] == "lora" and "coco" in r["conf"].lower()),
        "adapter": agg(lambda r: r["family"] == "adapter"),
        "full_ft": agg(lambda r: r["family"] == "full_ft"),
    }
    print(f"\n  {'subset':<14} {'n':>4} {'mean':>8} {'sd':>7} {'min':>7} {'max':>7}   旧台账")
    for k, v in subsets.items():
        o = old.get("subsets", {}).get(k, {})
        print(f"  {k:<14} {v['n']:>4} {v.get('mean', float('nan')):>8.4f} {v.get('sd', float('nan')):>7.4f} "
              f"{v.get('min', float('nan')):>7.4f} {v.get('max', float('nan')):>7.4f}   "
              f"n={o.get('n')}, mean={o.get('mean')}")

    n_neg = sum(1 for r in runs if r["alpha"] < 0)
    print(f"\n  alpha < 0: {n_neg}/{len(runs)}")
    print(f"  manuscript claims: 162 ODE fits, '215 fits / 196 negative alpha', '19 exceptions'")
    print(f"  reproducible from archives: {len(runs)} fits; gap to 162 = {162 - len(runs)}")

    if a.apply:
        out = {"caliber": "per-run", "scope": "all outputs/**/dg_star_history.json with >=5 epochs",
               "n_runs_total": len(runs), "skipped_short": skipped_short, "subsets": subsets,
               "alpha_negative": n_neg, "runs": runs,
               "claimed_in_manuscript": 162, "gap_to_claim": 162 - len(runs)}
        io.open(LEDGER, "w", encoding="utf-8", newline="").write(json.dumps(out, ensure_ascii=False, indent=1))
        print(f"\n  wrote {LEDGER.relative_to(REPO)}")
    else:
        print("\n  (dry run; --apply writes outputs/analysis/ode_ledger_all.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

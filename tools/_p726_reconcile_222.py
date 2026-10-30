# -*- coding: utf-8 -*-
r"""Reconcile the 222 vs 215 discrepancy in Paper A's alpha statistics.

Paper A says: "Across the 222 fits we archived, alpha < 0 in 203 ... 19 exceptions are ten of the
fifty Adapter fits, four LoRA fits, and all three CLIP BitFit fits."

outputs/analysis/alpha_sign_audit.json records, for ode_ledger.json, n = 103 with 4 non-negative.
The current ode_ledger.json holds 96 runs. So the audit predates a recomputation of the ledger.

This establishes, from the data:
  - how many runs each population actually holds now
  - what the sum is now (the number a reviewer would get)
  - whether the audit's 103 is explainable (e.g. superseded or duplicate configurations)
  - therefore what the correct sentence in the paper is.

    python tools/_p726_reconcile_222.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    led = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    aud = json.loads((PUB / "outputs/analysis/alpha_sign_audit.json").read_text(
        encoding="utf-8", errors="ignore"))

    print("=" * 112)
    print("1. ode_ledger.json now")
    print("=" * 112)
    print(f"  n_runs_total   = {led.get('n_runs_total')}")
    print(f"  len(runs)      = {len(led.get('runs') or [])}")
    print(f"  subsets.all.n  = {led['subsets']['all']['n']}")
    runs = led.get("runs") or []
    print(f"  families       = {dict(Counter(r.get('family') for r in runs))}")
    neg = [r for r in runs if isinstance(r.get("alpha"), (int, float)) and r["alpha"] < 0]
    nonneg = [r for r in runs if isinstance(r.get("alpha"), (int, float)) and r["alpha"] >= 0]
    print(f"  alpha < 0      = {len(neg)}   alpha >= 0 = {len(nonneg)}")
    print(f"  non-negative examples: "
          f"{[(r.get('conf'), round(r['alpha'], 6)) for r in nonneg]}")

    print()
    print("=" * 112)
    print("2. what the audit recorded (a snapshot of an earlier ledger)")
    print("=" * 112)
    for k, v in aud.items():
        if isinstance(v, dict) and "n" in v:
            print(f"  {k}")
            print(f"     n={v['n']}  neg={v['neg']}  nonneg={v['nonneg']}  max={v.get('max')}")

    print()
    print("=" * 112)
    print("3. the population now, and the sum a reviewer would compute")
    print("=" * 112)
    pops = {
        "ode_ledger.json": len(runs),
        "ode_loco.json": None,
        "ode_loco2.json": None,
        "theory/adapter/adapter_all_results.json": None,
        "theory/bitfit/bitfit_results.json": None,
    }
    for rel, key in (("outputs/analysis/ode_loco.json", "per_config"),
                     ("outputs/analysis/ode_loco2.json", "per_config")):
        d = json.loads((PUB / rel).read_text(encoding="utf-8", errors="ignore"))
        pops[rel.split("/")[-1]] = len(d.get(key) or {})
    ad = json.loads((PUB / "outputs/theory/adapter/adapter_all_results.json").read_text(
        encoding="utf-8", errors="ignore"))
    bf = json.loads((PUB / "outputs/theory/bitfit/bitfit_results.json").read_text(
        encoding="utf-8", errors="ignore"))
    pops["theory/adapter/adapter_all_results.json"] = len(ad)
    pops["theory/bitfit/bitfit_results.json"] = len(bf)
    total_now = 0
    for k, v in pops.items():
        print(f"     {v:>5}   {k}")
        total_now += v or 0
    print(f"     -----")
    print(f"     {total_now:>5}   TOTAL NOW  (the audit said 222)")

    print()
    print("=" * 112)
    print("4. can the audit's ledger n = 103 be explained?")
    print("=" * 112)
    print(f"  audit n for ode_ledger = 103; ledger now = {len(runs)}; "
          f"difference = {103 - len(runs)}")
    # are there duplicate configurations in the current ledger?
    confs = Counter(r.get("conf") for r in runs)
    dupes = {k: v for k, v in confs.items() if v > 1}
    print(f"  duplicated confs in the current ledger: {len(dupes)} "
          f"(total extra rows: {sum(v - 1 for v in dupes.values())})")
    # top-level bookkeeping
    print(f"  n_configs = {led.get('n_configs')}, n_configs_lora = {led.get('n_configs_lora')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""Compute the alpha-sign statistics from the archive as it now stands, so the paper can state them.

The paper says "across the 222 fits we archived, alpha < 0 in 203; the 19 exceptions are ten of the
fifty Adapter fits (largest +0.061), four LoRA fits (largest +0.011) and all three CLIP BitFit
fits". The audit agrees (222 / 203 / 19).

After fixing the .gitignore anchoring, the archive holds 96 dg_star_history.json files in
outputs/theory (87 before), and the five source populations sum to 215 rather than 222. The seven
missing runs predate the repository and cannot be recovered from it.

This computes the current numbers exactly, including the exception breakdown by family, so the
paper's sentence can be rewritten to what the archive supports - or the discrepancy declared.

    python tools/_p732_alpha_stats_now.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "alpha_stats_current.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rows = []

    def add(source, family, alpha):
        rows.append({"source": source, "family": family, "alpha": alpha})

    led = json.loads((PUB / "outputs/analysis/ode_ledger.json").read_text(
        encoding="utf-8", errors="ignore"))
    for r in led.get("runs") or []:
        add("ode_ledger.json", str(r.get("family")), r.get("alpha"))

    for rel, path, fam in (("outputs/analysis/ode_loco.json", "per_config", "loco"),
                           ("outputs/analysis/ode_loco2.json", "per_config", "loco2")):
        d = json.loads((PUB / rel).read_text(encoding="utf-8", errors="ignore"))
        for k, v in (d.get(path) or {}).items():
            if isinstance(v, dict):
                add(rel.split("/")[-1], fam, v.get("alpha"))

    for rel, fam, key in (("outputs/theory/adapter/adapter_all_results.json", "adapter", "alpha"),
                          ("outputs/theory/bitfit/bitfit_results.json", "bitfit", "alpha")):
        for e in json.loads((PUB / rel).read_text(encoding="utf-8", errors="ignore")):
            add(rel.split("/")[-1], fam, e.get(key))

    vals = [r for r in rows if isinstance(r["alpha"], (int, float))]
    neg = [r for r in vals if r["alpha"] < 0]
    nonneg = [r for r in vals if r["alpha"] >= 0]
    print("=" * 104)
    print("alpha sign statistics, archive as it now stands")
    print("=" * 104)
    print(f"  total fits with an alpha        = {len(vals)}")
    print(f"  alpha < 0                       = {len(neg)}")
    print(f"  alpha >= 0 (the exceptions)     = {len(nonneg)}")
    print(f"  largest exception               = {max(r['alpha'] for r in nonneg):+.6f}")
    print()
    print("  exceptions by source:")
    by_src = defaultdict(list)
    for r in nonneg:
        by_src[r["source"]].append(r["alpha"])
    for k, v in sorted(by_src.items()):
        print(f"     {k:<34} {len(v):>3}  largest {max(v):+.6f}")
    print()
    print("  exceptions by family:")
    by_fam = defaultdict(list)
    for r in nonneg:
        by_fam[r["family"]].append(r["alpha"])
    for k, v in sorted(by_fam.items()):
        print(f"     {k:<20} {len(v):>3}  largest {max(v):+.6f}")
    print()
    print("  population by source:")
    pop = Counter(r["source"] for r in vals)
    for k, v in sorted(pop.items()):
        n_neg = sum(1 for r in vals if r["source"] == k and r["alpha"] < 0)
        print(f"     {k:<34} n={v:>3}  neg={n_neg:>3}  nonneg={v-n_neg:>2}")

    print()
    print("=" * 104)
    print("what the paper says vs what the archive supports")
    print("=" * 104)
    print(f"  paper: 222 fits, 203 negative, 19 exceptions "
          f"(10 Adapter, 4 LoRA, 3 BitFit, largest +0.061)")
    print(f"  audit: 222 fits, 203 negative, 19 exceptions")
    print(f"  now  : {len(vals)} fits, {len(neg)} negative, {len(nonneg)} exceptions")
    print()
    print("  => the seven-run difference is not recoverable from the repository:")
    print("     outputs/analysis/ode_ledger.json has exactly one commit, made when it")
    print("     already held 96 runs, so the 103-run revision the audit saw never existed")
    print("     in the published archive.")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"total": len(vals), "negative": len(neg), "exceptions": len(nonneg),
             "exceptions_by_source": {k: len(v) for k, v in by_src.items()},
             "exceptions_by_family": {k: len(v) for k, v in by_fam.items()},
             "population_by_source": dict(pop)},
            ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

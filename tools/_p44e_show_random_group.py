#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44e_show_random_group.py -- print the exact Random-group run list with ranks."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "outputs/analysis/p3_stats_recon.json"), encoding="utf-8"))
rows = [r for r in D["runs"] if r.get("group") == "Random"]
print("Random group: n=%d" % len(rows))
for r in rows:
    print("  %-14s rank=%-3s seed=%-5s dE=%s" %
          (r["name"], r["rank"], r["seed"], ("NaN" if r["dE"] is None else round(r["dE"], 1))))
H = json.load(open(os.path.join(ROOT, "outputs/analysis/p3_stats_hardened.json"), encoding="utf-8"))
cf = H["counterfactual"]["Random"]
print("\narchive-derived: n_runs=%s n_nan=%s nan_runs=%s n_by_rank=%s" %
      (cf["n_runs"], cf["n_nan"], cf["nan_run_names"], cf["n_by_rank"]))
print("finite n=%s values=%s" % (cf["finite_only"]["n"], sorted(cf["finite_only"]["values"])))
print("median(finite)=%s  median(nan_as_zero)=%s" %
      (cf["finite_only"]["median"], H.get("counterfactual", {}).get("Random", {}).get("median_nan_as_zero")))

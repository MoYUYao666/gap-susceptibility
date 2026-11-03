#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44p_verify_paired_ci.py -- reconcile the paired-difference CI for the 10-seed
family: t-interval vs bootstrap percentile.  The Lead quoted [+66.0, +135.2].

Also pins down the E0-cluster composition of the paper's own 3 seeds."""
import json, os
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(ROOT, "outputs/analysis/p3_multiseed_family.json"), encoding="utf-8"))
pairs = M["paired_seed_r6_vs_r5"]["pairs"]
d = np.asarray([p["diff"] for p in pairs], dtype=float)
r5 = np.asarray([p["r5"] for p in pairs], dtype=float)
r6 = np.asarray([p["r6"] for p in pairs], dtype=float)
n = d.size
print("n pairs = %d ; mean diff = %.2f ; sd = %.2f" % (n, d.mean(), d.std(ddof=1)))

t = stats.t.interval(0.95, n - 1, loc=d.mean(), scale=stats.sem(d))
print("t-interval  95%% CI = [%.2f, %.2f]" % (t[0], t[1]))

for seed in (20261012, 0, 1, 42):
    rng = np.random.default_rng(seed)
    bs = d[rng.integers(0, n, size=(20000, n))].mean(axis=1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print("bootstrap percentile CI (seed=%d) = [%.2f, %.2f]" % (seed, lo, hi))

# how many of the 10 seeds sit in each E0 cluster, and where do the paper's 3 fall?
print("\n--- E0 cluster membership ---")
by_seed = {}
for p in M["paired_seed_r6_vs_r5"]["pairs"]:
    # E0 is not in the pairs; pull from the stratified records
    pass
fam = M["family"]["E0_clusters"]
for k, v in fam.items():
    print("  %-14s seeds=%s" % (k, sorted(v)))
paper = [42, 123, 999]
for c, seeds in fam.items():
    inter = sorted(set(seeds) & set(paper))
    if inter:
        print("  paper seeds in %-12s : %s (%d of 3)" % (c, inter, len(inter)))

# cluster means for r5 from the stratified block
st = M["stratified_by_E0_cluster"]["r5"]["clusters"]
print("\n--- r=5 by E0 cluster (from archive) ---")
for e0, s in sorted(st.items()):
    print("  E0=%-8s n=%d mean=%+.2f  CI=[%.2f,%.2f]  positive=%d/%d  seeds=%s"
          % (e0, s["n"], s["mean"], s["mean_boot_ci95"][0], s["mean_boot_ci95"][1],
             s["n_positive"], s["n"],
             sorted(int(x.split("_s")[1].split(".")[0]) for x in s["sources"])))
st6 = M["stratified_by_E0_cluster"]["r6"]["clusters"]
print("--- r=6 by E0 cluster ---")
for e0, s in sorted(st6.items()):
    print("  E0=%-8s n=%d mean=%+.2f  CI=[%.2f,%.2f]  positive=%d/%d"
          % (e0, s["n"], s["mean"], s["mean_boot_ci95"][0], s["mean_boot_ci95"][1],
             s["n_positive"], s["n"]))

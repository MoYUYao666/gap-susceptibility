#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1648_probe_bootstrap_variants.py -- explain the small CI difference between the cloud
aggregate's accuracy contrast and _p1647's recomputation.

Deltas match exactly; the interval bounds differ in the third decimal.  Candidates:
  A. idx shape (n_boot, n) vs (n, n_boot)
  B. percentile 5/95 (archived) vs 2.5/97.5
  C. RandomState vs default_rng
  D. RNG advanced by earlier draws (one RNG for all three pairs)
  E. rng.choice without replacement / with replacement
"""
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANA = ROOT / "outputs/analysis"
SEED = 20261024
NBOOT = 20000
MARGIN = 0.05


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module("vqa1516_metrics", str(ROOT / "tools/_p1516_p3_vqa_downstream.py"))
norm = mod.norm


def arm(tag):
    d = json.loads((ANA / ("p3_second_downstream_%s.json" % tag)).read_text(encoding="utf-8"))
    nref = [norm(x) for x in d["refs"]]
    nhyp = [norm(x) for x in d["hypotheses"]]
    return np.array([1.0 if a == b else 0.0 for a, b in zip(nhyp, nref)])


base, r5 = arm("base"), arm("5")
agg = json.loads((ANA / "p3_second_downstream.json").read_text(encoding="utf-8"))
want = agg["contrasts"]["base_minus_5"]["accuracy"]
print("archived base_minus_5 accuracy: delta=%+0.6f ci95=[%+0.6f,%+0.6f]"
      % (want["delta"], want["ci95"][0], want["ci95"][1]))
print("observed delta = base - r5 = %+0.6f" % (base.mean() - r5.mean()))

delta = base.mean() - r5.mean()
n = len(base)


def report(tag, d):
    print("  %-46s [%+0.6f,%+0.6f]  EXACT MATCH" % (tag, np.percentile(d, 5.0),
                                                      np.percentile(d, 95.0))
          if abs(np.percentile(d, 5.0) - want["ci95"][0]) < 5e-6 else
          "  %-46s [%+0.6f,%+0.6f]" % (tag, np.percentile(d, 5.0), np.percentile(d, 95.0)))


# A: default_rng, idx (n_boot, n), pct 5/95
rng = np.random.default_rng(SEED)
idx = rng.integers(0, n, size=(NBOOT, n))
report("A default_rng (n_boot,n) pct5/95", base[idx].mean(1) - r5[idx].mean(1))

# B: percentiles 2.5/97.5
report("A bounds but pct2.5/97.5", base[idx].mean(1) - r5[idx].mean(1))

# C: RandomState
rs = np.random.RandomState(SEED)
idx2 = rs.randint(0, n, size=(NBOOT, n))
report("C RandomState (n_boot,n)", base[idx2].mean(1) - r5[idx2].mean(1))

# D: idx (n, n_boot)
rng = np.random.default_rng(SEED)
idxt = rng.integers(0, n, size=(n, NBOOT))
report("D default_rng (n,n_boot) transposed means", base[idxt].mean(0) - r5[idxt].mean(0))

# E: choice
rng = np.random.default_rng(SEED)
idxc = rng.choice(n, size=(NBOOT, n), replace=True)
report("E default_rng choice", base[idxc].mean(1) - r5[idxc].mean(1))

# F: 10% trimmed / other percentiles used by some vqa_contrast variants
d = base[idx].mean(1) - r5[idx].mean(1)
for lo, hi in ((2.5, 97.5), (5, 95), (1, 99)):
    print("  percentile variant %-5s %-5s -> [%+0.6f,%+0.6f]"
          % (lo, hi, np.percentile(d, lo), np.percentile(d, hi)))

# G: maybe the aggregate resampled WITH the metric-normalised arrays from a different norm
print("\n  archived ci width = %.6f ; A width = %.6f"
      % (want["ci95"][1] - want["ci95"][0],
         np.percentile(d, 95.0) - np.percentile(d, 5.0)))
print("  archived boot_mean=%s boot_se=%s" % (want.get("boot_mean"), want.get("boot_se")))
rng = np.random.default_rng(SEED)
idx = rng.integers(0, n, size=(NBOOT, n))
d = base[idx].mean(1) - r5[idx].mean(1)
print("  A boot_mean=%.10f boot_se=%.10f" % (d.mean(), d.std(ddof=1)))


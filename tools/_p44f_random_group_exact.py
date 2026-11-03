#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44f_random_group_exact.py -- exact Random-group table straight from the archive.

Corrects the hand-written table: the archive order is R_s42_d{0,1,2},
R_s123_d{0,1,2}, R_s456_d{0,1,2}, R_s789_d{0,1,2}, R_s999_d{0,1,2}.
"""
import json, math, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "paper3/scripts/outputs/experiments/all_results.json")
D = json.load(open(P, encoding="utf-8"))


def fin(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


print("=== Random group, exact archive order ($.Random[*]) ===")
print("%-14s %-6s %-6s %s" % ("name", "rank", "seed", "dE"))
vals, nan_names = [], []
for i, r in enumerate(D["Random"]):
    E = r["E"]
    dE = (E[-1] - E[0]) if (len(E) >= 2 and fin(E[-1]) and fin(E[0])) else None
    print("%-14s %-6s %-6s %s" % (r["name"], r["rank"], r["seed"],
                                  ("NaN" if dE is None else "%+.1f" % dE)))
    if dE is None:
        nan_names.append(r["name"])
    else:
        vals.append(dE)

ranks = [r["rank"] for r in D["Random"]]
print("\nrank sequence:", ranks)
print("rank counts:", {k: ranks.count(k) for k in sorted(set(ranks))})
print("NaN runs:", nan_names)
print("finite n=%d" % len(vals))
print("finite values sorted:", sorted(vals))
a = np.asarray(vals, dtype=float)
print("mean=%.2f  sample sd=%.2f  population sd=%.2f" % (a.mean(), a.std(ddof=1), a.std(ddof=0)))
print("median(finite)=%.2f" % np.median(a))
b = np.asarray(vals + [0.0, 0.0], dtype=float)
print("median(NaN->0, n=%d)=%.2f  -> equals finite median: %s"
      % (b.size, np.median(b), bool(np.median(b) == np.median(a))))
print("\nrank-4 only (Theory's matched rank):")
r4 = np.asarray([v for v, rk in zip(vals, [r["rank"] for r in D["Random"] if fin(r["E"][-1])])
                 if rk == 4], dtype=float)

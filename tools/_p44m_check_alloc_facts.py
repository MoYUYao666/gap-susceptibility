#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44m_check_alloc_facts.py -- verify the three facts p3-allocation reported,
so the report can cite them with a real provenance trail (not hearsay)."""
import json, os, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def L(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


print("=== 1. ode_ledger.json beta ===")
ol = L("outputs/analysis/ode_ledger.json")
runs = ol.get("runs", [])
betas = [r.get("beta") for r in runs if isinstance(r.get("beta"), (int, float))]
print("  total runs=%d ; runs with beta=%d" % (len(runs), len(betas)))
print("  median beta = %.9f" % st.median(betas))
print("  runs[90].beta = %r" % (runs[90].get("beta") if len(runs) > 90 else None))
print("  runs[90].conf = %r" % (runs[90].get("conf") if len(runs) > 90 else None))
print("  runs[90].family = %r" % (runs[90].get("family") if len(runs) > 90 else None))
n137 = sum(1 for b in betas if abs(b - 0.1371162965748463) < 1e-12)
print("  runs whose beta == 0.1371162965748463 exactly: %d" % n137)

print("\n=== 2. gamma_llava_results.json: E_mean / CE_loss_mean per rank ===")
g = L("paper3/scripts/outputs/experiments/gamma_llava_results.json")
for rk, v in g["results_by_rank"].items():
    print("  %-4s E_mean=%s CE_loss_mean=%s" % (rk, v.get("E_mean"), v.get("CE_loss_mean")))

print("\n=== 3. p3_alloc_budget_probe.json ===")
bp = L("outputs/analysis/p3_alloc_budget_probe.json")


def find_key(o, key, path="", out=None):
    if out is None:
        out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                out.append((path + "." + k, v))
            find_key(v, key, path + "." + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            find_key(v, key, path + "[%d]" % i, out)
    return out


for key in ("excluded_patch_embed_params", "cost_model_verified", "per_rank_cost",
            "cost_per_rank", "block_cost"):
    hits = find_key(bp, key)
    if hits:
        for h in hits[:3]:
            print("  %s = %s" % (h[0], json.dumps(h[1])[:400]))

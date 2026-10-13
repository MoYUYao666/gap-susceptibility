#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p447_show_gamma_batches.py -- extract the archived cross-batch Gamma data.

outputs/llava_gamma_batches.json (produced by tools/llava_gamma_batch_ci.py) holds
per-sample per-block <grad E, grad L> for 6 independent sample windows of 16.
That is exactly the raw material R3.4 asks for: how sensitive is Gamma_k to the
choice and size of the reference batch.
"""
import json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "outputs", "llava_gamma_batches.json")
with open(P, encoding="utf-8") as f:
    D = json.load(f)

print("keys:", list(D.keys()))
print("n_batches:", D["n_batches"], "batches:", D["batches"], "n_per_batch:", D["n_per_batch"])
print("blocks:", D["blocks"])
print("protocol:", D["protocol"])
print()
print("block_cross_batch:")
for b, v in D["block_cross_batch"].items():
    print("   %-12s mean=%12s std=%10s ci95=%s cv%%=%s" % (b, v["mean"], v["std"], v["ci95"], v["cv_pct"]))
print()
print("block_hierarchical_bootstrap:")
for b, v in D["block_hierarchical_bootstrap"].items():
    print("   %-12s mean=%12s ci95=%s" % (b, v["mean"], v["ci95"]))
print()
print("argmax_freq:", D["argmax_freq"])
print("argmin_freq:", D["argmin_freq"])
print()
print("alloc_per_batch:", json.dumps(D["alloc_per_batch"], indent=1))
print()
print("alloc_bootstrap_top:")
for r in D["alloc_bootstrap_top"]:
    print("  ", r)
print()
print("pairwise_spearman:", D["pairwise_spearman"])
print()
# per-batch per-block means recomputed from raw
raw = D["raw_per_sample_blocks"]
print("per-batch per-block means (recomputed from raw_per_sample_blocks):")
for k in raw:
    arr = {b: np.mean([s.get(b, 0.0) for s in raw[k]]) for b in D["blocks"]}
    print("   batch %-4s %s" % (k, {kk: round(vv, 1) for kk, vv in arr.items()}))

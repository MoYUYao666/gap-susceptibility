# -*- coding: utf-8 -*-
"""Summarize the Qwen per-layer coupling: normalized shares and group comparison."""
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
d = json.load(io.open(os.path.join(AN, "p3_qwen_perlayer_gamma.json"), encoding="utf-8"))["layers"]
keys = sorted(d)
vals = np.array([d[k]["mean"] for k in keys])
absv = np.abs(vals)
share = absv / absv.sum()
out = {"meta": {"script": "tools/_p1571_qwen_perlayer_summary.py", "source": "p3_qwen_perlayer_gamma.json"},
       "n_layers": len(keys),
       "median": float(np.median(vals)),
       "share": {k: float(s) for k, s in zip(keys, share)},
       "first4_share": float(share[:4].sum()),
       "top3": [{"layer": k, "mean": float(d[k]["mean"]), "share": float(s)}
                for k, s in sorted(zip(keys, share), key=lambda kv: -kv[1])[:3]],
       "near_zero_tail": int((share < 1e-6).sum())}
json.dump(out, io.open(os.path.join(AN, "p3_qwen_perlayer_summary.json"), "w", encoding="utf-8"), indent=1)
print("first4 share %.3f top3 %s tail %d" % (out["first4_share"], [(t["layer"], round(t["share"], 3)) for t in out["top3"]], out["near_zero_tail"]))

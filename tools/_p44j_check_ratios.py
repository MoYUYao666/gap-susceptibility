#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44j_check_ratios.py -- verify the paper's derived ratios (46x, 2.7x) against
the archive, so the report does not repeat an unverified claim."""
import json, math, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E2 = json.load(open(os.path.join(ROOT, "paper3/scripts/outputs/experiments/E2_results.json"), encoding="utf-8"))
QW = json.load(open(os.path.join(ROOT, "paper3/scripts/outputs/experiments/Qwen_results.json"), encoding="utf-8"))


def fin(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def means(d, key, ranks):
    out = {}
    for rk in ranks:
        vals = [e["E"][-1] - e["E"][0] for e in d.get(key, [])
                if e.get("rank") == rk and len(e.get("E", [])) >= 2 and fin(e["E"][-1])]
        if vals:
            out[rk] = float(np.mean(vals))
    return out


print("=== LLaVA '46x surge' ===")
llava = {}
llava.update(means(E2, "E2", [4, 16]))
llava.update(means(E2, "extra", [5, 6, 7, 8]))
llava.update(means(E2, "sweep", [20]))
for rk in sorted(llava):
    print("  r=%-3d mean=%+9.1f" % (rk, llava[rk]))
if 6 in llava and 20 in llava:
    print("  |dE(20)| / |dE(6)|  = %.1f  <-- paper says 46x" % (abs(llava[20]) / abs(llava[6])))
if 4 in llava and 20 in llava:
    print("  |dE(20)| / |dE(4)|  = %.1f" % (abs(llava[20]) / abs(llava[4])))

print("\n=== Qwen '2.7x gradual increase' ===")
qwen = means(QW, "sweep", list(range(0, 100)))
qwen = {rk: v for rk, v in qwen.items() if rk in (4, 6, 8, 16, 20, 24, 28, 32, 48, 64)}
for rk in sorted(qwen):
    print("  r=%-3d mean=%+9.1f" % (rk, qwen[rk]))
if 6 in qwen and 64 in qwen:
    print("  dE(64)/dE(6) = %.2f  <-- paper says 2.7x" % (qwen[64] / qwen[6]))
if 4 in qwen and 64 in qwen:
    print("  dE(64)/dE(4) = %.2f" % (qwen[64] / qwen[4]))
print("\n  Qwen max/min over ranks 4..64: %.1f / %.1f = %.2f"
      % (max(qwen.values()), min(qwen.values()), max(qwen.values()) / min(qwen.values())))

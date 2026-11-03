#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p442_inspect_json.py -- dump the raw structure of the key P3 archives so that
every downstream statistic can name file + field."""
import json, os, sys, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def show(rel, maxdepth=3, maxitems=8):
    p = os.path.join(ROOT, rel)
    print("=" * 78)
    print(rel, "exists=", os.path.exists(p))
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        o = json.load(f)

    def rec(x, d=0, key=""):
        pad = "  " * d
        if d > maxdepth:
            return
        if isinstance(x, dict):
            ks = list(x.keys())
            print("%s%s{ } keys=%d: %s" % (pad, key + " " if key else "", len(ks), ks[:maxitems]))
            for k in ks[:maxitems]:
                rec(x[k], d + 1, k)
        elif isinstance(x, list):
            print("%s%s[ ] len=%d" % (pad, key, len(x)))
            for i, v in enumerate(x[:maxitems]):
                rec(v, d + 1, "[%d]" % i)
        else:
            s = repr(x)
            print("%s%s = %s" % (pad, key, s[:160]))
    rec(o, 0, "")
    return o


if __name__ == "__main__":
    for rel in ["paper3/scripts/outputs/experiments/all_results.json",
                "paper3/scripts/outputs/experiments/gamma_llava_results.json",
                "paper3/scripts/outputs/experiments/sample_size_results.json",
                "paper3/scripts/outputs/experiments/qwen_gamma_fp32_verify.json",
                "paper3/scripts/outputs/experiments/vqa_phase_results.json",
                "paper3/scripts/outputs/experiments/ers_1epoch_results.json"]:
        show(rel)

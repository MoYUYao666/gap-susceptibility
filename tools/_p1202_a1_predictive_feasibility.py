# -*- coding: utf-8 -*-
"""Inspect the two A1 archives that decide whether an out-of-family prediction is feasible without new runs."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def walk(o, prefix="", depth=0, maxd=3):
    if depth > maxd:
        return
    if isinstance(o, dict):
        for k, v in list(o.items())[:10]:
            if isinstance(v, dict):
                print(f"     {prefix}{k}: dict({len(v)})")
                walk(v, prefix + k + ".", depth + 1, maxd)
            elif isinstance(v, list):
                print(f"     {prefix}{k}: list({len(v)})"
                      + (f" item0 keys={list(v[0])[:8]}" if v and isinstance(v[0], dict) else
                         f" item0={str(v[0])[:40]}" if v else ""))
            else:
                print(f"     {prefix}{k} = {str(v)[:70]}")


for rel in ("outputs/a1_theory_verify.json", "outputs/a1_tau_holdout.json", "outputs/a1_rr_e4_eval_archived.json"):
    p = os.path.join(REPO, rel)
    print(f"=== {rel} ({os.path.getsize(p)} B)")
    d = json.load(io.open(p, encoding="utf-8"))
    walk(d)
    print()

# what does margins.json hold?
for rel in ("outputs/a1_margins.json", "outputs/a1_h_templates.json"):
    p = os.path.join(REPO, rel)
    d = json.load(io.open(p, encoding="utf-8"))
    print(f"=== {rel} ({os.path.getsize(p)//1024} KB) ===")
    if isinstance(d, dict):
        print("   top keys:", list(d)[:10])
        for k, v in list(d.items())[:3]:
            if isinstance(v, (list, dict)):
                print(f"   {k}: {type(v).__name__}({len(v)})")
                if isinstance(v, dict):
                    print("      child:", list(v)[:8])
                elif v and isinstance(v[0], dict):
                    print("      item0:", {kk: str(vv)[:30] for kk, vv in list(v[0].items())[:8]})
            else:
                print(f"   {k} = {str(v)[:70]}")

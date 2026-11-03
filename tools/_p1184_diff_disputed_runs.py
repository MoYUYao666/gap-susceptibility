# -*- coding: utf-8 -*-
r"""Locate the archived runs behind the two disputed text-only numbers and diff their recorded metadata.

Paper A states that the earlier +0.079 belongs to "a different configuration (alpha=64, R@1 0.389)" and withdraws it,
while the text-only arm reports -0.081 with R@1 0.637 at alpha=64 elsewhere. The reviewer's central complaint was
precisely that apparently identical configurations disagree, so this script finds both archives and prints, field by
field, what actually differs between them.

Read-only. Nothing is written.

    python tools/_p1184_diff_disputed_runs.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(f):
    try:
        return json.load(io.open(f, encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def r1_of(d):
    if not isinstance(d, dict):
        return None
    m = d.get("final_task_metrics") or {}
    for k in ("R@1", "r1", "R1"):
        if k in m:
            return m[k]
    if "R@1" in d:
        return d["R@1"]
    return None


def cg_delta(d):
    if not isinstance(d, dict):
        return None
    a = d.get("initial_gap") or {}
    b = d.get("final_gap") or {}
    if "centroid_gap" in a and "centroid_gap" in b:
        return b["centroid_gap"] - a["centroid_gap"]
    return None


def main() -> None:
    print("  scanning outputs/**/results.json for R@1 near 0.637 and CGdelta near -0.081 ...\n")
    cands = []
    for f in glob.glob(os.path.join(REPO, "outputs", "**", "results.json"), recursive=True):
        d = load(f)
        r1 = r1_of(d)
        cg = cg_delta(d)
        if r1 is None or cg is None:
            continue
        if abs(r1 - 0.637) < 0.004 or abs(cg + 0.081) < 0.004:
            cands.append((f, r1, cg, d))
    print(f"  candidates: {len(cands)}")
    for f, r1, cg, d in sorted(cands, key=lambda x: -abs(x[1] - 0.637))[:8]:
        rel = os.path.relpath(f, REPO)
        print(f"   {rel}\n     R@1={r1:.4f}  CGdelta={cg:+.4f}  params={d.get('n_trainable_params')}  "
              f"rank={d.get('lora_rank')}  experiment={d.get('experiment')}")

    # the Route D run the paper withdraws
    target = os.path.join(REPO, "outputs", "route_d", "d1_alpha64_text_r8", "results.json")
    d1 = load(target)
    print("\n=== Route D d1_alpha64_text_r8 (the withdrawn +0.079) ===")
    if d1:
        print(f"  R@1={r1_of(d1):.4f}  CGdelta={cg_delta(d1):+.4f}  params={d1.get('n_trainable_params')}  "
              f"rank={d1.get('lora_rank')}")
        print(f"  keys: {sorted(d1)}")
        for k in ("final_val_loss", "final_train_loss", "seed", "target_modules", "dataset"):
            if k in d1:
                print(f"  {k} = {d1[k]}")

    # compare against the closest candidate
    if cands:
        f, r1, cg, d = sorted(cands, key=lambda x: (abs(x[1] - 0.637) + abs(x[2] + 0.081)))[0]
        print(f"\n=== closest core candidate: {os.path.relpath(f, REPO)} ===")
        print(f"  R@1={r1:.4f}  CGdelta={cg:+.4f}  params={d.get('n_trainable_params')}  rank={d.get('lora_rank')}")
        print(f"  keys: {sorted(d)}")
        for k in ("final_val_loss", "final_train_loss", "seed", "target_modules", "dataset", "experiment"):
            if k in d:
                print(f"  {k} = {d[k]}")
        if d1:
            print("\n=== field-by-field diff (d1 vs candidate) ===")
            keys = sorted(set(d1) | set(d))
            for k in keys:
                a, b = d1.get(k), d.get(k)
                if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
                    continue
                if a != b:
                    print(f"   {k}: d1={a!r}  cand={b!r}")


if __name__ == "__main__":
    main()

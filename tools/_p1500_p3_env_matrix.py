# -*- coding: utf-8 -*-
r"""Assemble the software/seed reproducibility matrix for P3 (R1 comment R3.18).

Reads the archived run records only; no new compute.

    python tools/_p1500_p3_env_matrix.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_environment_matrix.json")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def main() -> int:
    seeds = {}
    for f in glob.glob(os.path.join(EXP, "p3_rerun_seeds*.json")) + glob.glob(os.path.join(EXP, "verify_r*_s*.json")):
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        r, s = d.get("rank"), d.get("seed")
        if r in (5, 6) and s in (42, 123, 456, 789, 999) and "delta_E" in d and not d.get("partial"):
            try:
                if d["delta_E"] is None or not (-1e6 < float(d["delta_E"]) < 1e6):
                    continue
            except Exception:
                continue
            seeds.setdefault(str(r), {})[str(s)] = d["delta_E"]
    tf = {}
    for f in sorted(glob.glob(os.path.join(EXP, "verify_r5_s42*.json"))):
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        tf[os.path.basename(f)] = {"delta_E": d.get("delta_E"), "note": (d.get("note") or "")[:160],
                                   "torch": d.get("torch"), "transformers": d.get("transformers")}
    env = {"meta": {"script": "tools/_p1500_p3_env_matrix.py", "task": "R1 R3.18 environment/seed matrix",
                    "hardware": "single RTX 4060 Laptop 8GB", "cuda": None, "torch": None}}
    try:
        import torch
        env["meta"]["torch"] = torch.__version__
        env["meta"]["cuda"] = torch.version.cuda
    except Exception as e:
        env["meta"]["torch_error"] = repr(e)
    env["seeds"] = seeds
    env["software_pairs"] = tf
    # same-seed spread per rank
    env["spread"] = {}
    for r, vals in seeds.items():
        xs = list(vals.values())
        if xs:
            env["spread"][r] = {"n": len(xs), "mean": sum(xs) / len(xs), "min": min(xs), "max": max(xs)}
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(env, indent=1))
    print("seeds:", {k: sorted(v) for k, v in seeds.items()})
    print("spread:", env["spread"])
    print("software pairs:", list(tf))
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

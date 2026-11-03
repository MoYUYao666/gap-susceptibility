#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Verify the smoke run: checkpoint non-empty, record carries both metric definitions.

This is the gate before the eight-hour retrain. Two independent facts must hold:

* the checkpoint's `model` dict holds the trainable tensors -- the defect of 2026-10-16 was that it was empty;
* the record JSON carries `dg_star_before/after`, `cg_canonical_*`, `dg_empirical_*` alongside the legacy keys.

    python tools/_p1123_verify_smoke.py   (runs on the host)
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import torch

OUT = Path("/root/p3/outputs/smoke_canonical")
KEYS = ("arm", "dg_star_before", "dg_star_after", "dg_star_rel_change",
        "cg_canonical_after", "dg_empirical_after", "dg_before", "dg_after", "dg_rel_change")


def main() -> int:
    ok = True
    pts = sorted(glob.glob(str(OUT / "*.pt")))
    if not pts:
        print("  FAIL no checkpoint written")
        ok = False
    for f in pts:
        obj = torch.load(f, map_location="cpu")
        model = obj.get("model", {})
        n = len(model)
        print(f"  {Path(f).name}: {Path(f).stat().st_size/1e6:.1f} MB | model tensors: {n}")
        for k, v in list(model.items())[:3]:
            print(f"      {k} {tuple(v.shape)}")
        if n == 0:
            print("  FAIL checkpoint is empty -- the 2026-10-16 defect is back")
            ok = False
        else:
            print("  PASS checkpoint holds trainable tensors")

    jsons = [j for j in glob.glob(str(OUT / "*.json"))
             if "progress" not in j and "sites" not in j]
    for j in jsons:
        d = json.load(open(j, encoding="utf-8"))
        print(f"\n  record {Path(j).name}:")
        for k in KEYS:
            v = d.get(k)
            flag = "PASS" if (k in d) else "FAIL"
            if flag == "FAIL":
                ok = False
            print(f"    {flag}  {k:<22} {v}")
        # canonical and legacy must not be the same numbers by construction
        if d.get("dg_star_before") is not None and d.get("dg_before") is not None:
            same = abs(d["dg_star_before"] - d["dg_before"]) < 1e-9
            print(f"    {'PASS' if not same else 'WARN'}  canonical differs from legacy: {not same}")

    print("\n  RESULT:", "READY to launch the retrain" if ok else "NOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Can the trained parameters be recovered from the optimiser state?

The saved checkpoints have `model: dict(0)` -- my filter for trainable tensors produced an empty dict -- but they
also contain `opt` with 28 MB (vision) to 188 MB (both) of state, which is the right size for two Adam moments
per trainable parameter. If `opt["param_groups"]` carries the parameter tensors themselves, the trained weights
are recoverable; if it carries only indices/ids, they are not, and a retrain is the only route.

This prints the structure precisely enough to decide.

    python tools/_p1114_probe_optimizer_state.py   (runs on the host)
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ADAPTERS = Path("/root/p3/adapters")


def main() -> int:
    f = ADAPTERS / "vision_only_s42_ckpt.pt"
    print(f"=== {f.name} ===")
    obj = torch.load(f, map_location="cpu")
    print("  top-level keys:", list(obj))

    opt = obj.get("opt", {})
    print("  opt keys:", list(opt))
    groups = opt.get("param_groups", [])
    print(f"  param_groups: {len(groups)}")
    for gi, g in enumerate(groups[:1]):
        print(f"    group {gi} keys: {list(g)}")
        for k, v in g.items():
            if isinstance(v, torch.Tensor):
                print(f"      {k}: tensor {tuple(v.shape)} {v.dtype}")
            elif isinstance(v, (list, tuple)):
                print(f"      {k}: list[{len(v)}] first={type(v[0]).__name__ if v else None}")
                if v and isinstance(v[0], torch.Tensor):
                    print(f"         first tensor: {tuple(v[0].shape)} {v[0].dtype}")
                    print(f"         data sample: {v[0].flatten()[:4].tolist()}")
            else:
                print(f"      {k}: {type(v).__name__} = {str(v)[:60]}")

    state = opt.get("state", {})
    print(f"  opt['state'] entries: {len(state)}")
    for k in list(state)[:2]:
        entry = state[k]
        print(f"    state[{k}] keys: {list(entry) if isinstance(entry, dict) else type(entry).__name__}")
        if isinstance(entry, dict):
            for k2, v2 in entry.items():
                if isinstance(v2, torch.Tensor):
                    print(f"      {k2}: tensor {tuple(v2.shape)} {v2.dtype}")
                else:
                    print(f"      {k2}: {type(v2).__name__} = {str(v2)[:40]}")

    # is there any tensor anywhere whose name hints at LoRA?
    names = []
    if groups:
        pg = groups[0]
        if "params" in pg:
            p = pg["params"]
            print(f"  params container: {type(p).__name__}, len {len(p) if hasattr(p, '__len__') else '?'}")
            if hasattr(p, "__len__") and len(p) and isinstance(p[0], torch.Tensor):
                print(f"    a parameter tensor: {tuple(p[0].shape)} {p[0].dtype}")
            elif hasattr(p, "__len__") and len(p):
                print(f"    first element type: {type(p[0]).__name__}")
    print("  conclusion:", "TENSORS PRESENT" if (groups and "params" in groups[0]
                                                and hasattr(groups[0]["params"], "__len__")
                                                and len(groups[0]["params"])
                                                and isinstance(groups[0]["params"][0], torch.Tensor))
          else "only indices/ids -- not recoverable")
    return 0


if __name__ == "__main__":
    sys.exit(main())

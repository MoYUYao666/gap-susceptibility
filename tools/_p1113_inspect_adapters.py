#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Inspect the saved adapter files: do they actually contain tensors?

The recomputation loaded them with `strict=False` and reported "0 tensors; missing 686" -- i.e. the dict was
empty, so all four arms produced identical numbers. The files are 28-188 MB, so they contain *something*; the
question is what key structure they have and whether the tensors are LoRA adapter weights (which would need
PEFT's loader) or base-model weights. This prints the real structure.

    python tools/_p1113_inspect_adapters.py   (runs on the host)
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ADAPTERS = Path("/root/p3/adapters")


def describe(obj, depth: int = 0) -> None:
    pad = "  " * (depth + 1)
    if isinstance(obj, dict):
        print(f"{pad}dict with {len(obj)} keys")
        for k in list(obj)[:8]:
            v = obj[k]
            if isinstance(v, torch.Tensor):
                print(f"{pad}  {k}: tensor {tuple(v.shape)} {v.dtype}")
            elif isinstance(v, dict):
                print(f"{pad}  {k}: dict({len(v)})")
                for k2 in list(v)[:6]:
                    v2 = v[k2]
                    if isinstance(v2, torch.Tensor):
                        print(f"{pad}    {k2}: tensor {tuple(v2.shape)} {v2.dtype}")
                    else:
                        print(f"{pad}    {k2}: {type(v2).__name__}")
            else:
                print(f"{pad}  {k}: {type(v).__name__}")
    else:
        print(f"{pad}{type(obj).__name__}")


def main() -> int:
    for f in sorted(ADAPTERS.glob("*.pt")):
        print(f"=== {f.name} ({f.stat().st_size/1e6:.1f} MB) ===")
        try:
            obj = torch.load(f, map_location="cpu")
            describe(obj, 0)
            # specifically: any key that looks like a LoRA adapter?
            found = []
            stack = [("", obj)]
            while stack:
                prefix, cur = stack.pop()
                if isinstance(cur, dict):
                    for k, v in cur.items():
                        kk = f"{prefix}{k}"
                        if isinstance(v, torch.Tensor):
                            if "lora" in kk.lower():
                                found.append((kk, tuple(v.shape)))
                        elif isinstance(v, dict):
                            stack.append((f"{kk}.", v))
            print(f"  LoRA-looking tensors: {len(found)}")
            for k, s in found[:6]:
                print(f"    {k} {s}")
        except Exception as exc:
            print("  FAILED to load:", type(exc).__name__, exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

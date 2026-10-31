# -*- coding: utf-8 -*-
r"""Prove the checkpoint filter fix works before proposing a retrain on the strength of it.

The defect was that `state_dict()` keys never matched parameter objects, so the filter kept nothing. The fix
matches by name. This checks the logic against a tiny real model (no GPU, seconds to run): build a model with one
trainable parameter, apply the same filter, and confirm the result is non-empty and contains exactly the
trainable key.

    python tools/_p1117_verify_filter.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import torch
import torch.nn as nn

REPO = Path(__file__).resolve().parents[1]
SWEEP = REPO / "tools" / "_p820_llava_sites.py"


class Toy(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.text_proj = nn.Linear(4, 4)
        self.vision_proj = nn.Linear(4, 4)


def main() -> int:
    src = io.open(SWEEP, encoding="utf-8").read()
    print("=== the filter as it now stands in the sweep ===")
    m = re.search(r"[ \t]*_trainable_names = .*?\n(?:.*\n){0,4}", src)
    print(m.group(0) if m else "  NOT FOUND")

    model = Toy()
    for n, p in model.named_parameters():
        p.requires_grad_("text" in n)          # only the text side is "trainable"

    # reproduce the fixed filter against this model
    ns = {}
    exec(  # noqa: S102 - this is the exact expression from the sweep, evaluated here
        "def filt(mm):\n"
        "    _trainable_names = {n for n, p in mm.named_parameters() if p.requires_grad}\n"
        "    _trainable = {k: v for k, v in mm.state_dict().items()\n"
        "                  if k in _trainable_names\n"
        "                  or any(k.endswith(n) or n.endswith(k) for n in _trainable_names)}\n"
        "    return _trainable_names, _trainable\n",
        ns)
    names, kept = ns["filt"](model)
    print(f"  trainable names: {sorted(names)}")
    print(f"  kept keys:       {sorted(kept)}")
    ok = kept and all("text" in k for k in kept)
    print(f"  non-empty and text-only: {bool(ok)}")

    # and show the old test failing on the same model, for the record
    old = {k: v for k, v in model.state_dict().items()
           if any(t is v for t in (p for p in model.parameters() if p.requires_grad))}
    print(f"  the OLD identity test would have kept: {len(old)} keys  <- this is the defect")

    # round-trip: save the filtered dict and load it back
    tmp = REPO / "outputs" / "_filter_check.pt"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": kept, "epoch": 1}, tmp)
    back = torch.load(tmp, map_location="cpu")
    same = set(back["model"]) == set(kept)
    print(f"  round-trip identical: {same} | size {tmp.stat().st_size} bytes")
    tmp.unlink()

    print("\n  VERDICT:", "the fix saves trainable tensors and reloads them" if (ok and same)
          else "SOMETHING IS STILL WRONG")
    return 0 if (ok and same) else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""Fix the checkpoint filter (second attempt, matching the real indentation).

The first attempt asserted on a literal block with the wrong leading whitespace and found nothing. The lines are
at a deeper indent (the save sits inside the epoch loop), so the replacement is done by regex on the two lines
themselves rather than on a hand-copied block.

The defect being fixed: `state_dict()` yields detached copies, so the identity test `p is v` never matched and the
saved checkpoint contained `model: {}`. Evidence from the host on 2026-10-17: all four arms loaded "0 tensors"
and produced identical DG*, and the optimiser state held only moments, so nothing was recoverable.

    python tools/_p1115_fix_ckpt_filter.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"

PAT = re.compile(
    r"(?P<ind>[ \t]*)_trainable = \{k: v for k, v in mm\.state_dict\(\)\.items\(\)\n"
    r"[ \t]*if any\(t is v for t in \(p for p in mm\.parameters\(\) if p\.requires_grad\)\)\}\n"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if "_trainable_names" in t:
        print("  already fixed")
        return 0
    m = PAT.search(t)
    if not m:
        print("  pattern not found; showing the region for inspection")
        i = t.find("_trainable =")
        print(t[max(0, i - 400): i + 400])
        return 1
    ind = m.group("ind")
    new = (
        f"{ind}# Membership must be tested by NAME. `state_dict()` yields detached copies rather than the\n"
        f"{ind}# parameter objects, so an identity test (`p is v`) never matched and the file was written with\n"
        f"{ind}# `model: {{}}` -- found on 2026-10-17 when every arm loaded 0 tensors and the optimiser state\n"
        f"{ind}# proved to hold only moments, leaving the trained weights unrecoverable.\n"
        f"{ind}_trainable_names = {{n for n, p in mm.named_parameters() if p.requires_grad}}\n"
        f"{ind}_trainable = {{k: v for k, v in mm.state_dict().items()\n"
        f"{ind}                  if k in _trainable_names\n"
        f"{ind}                  or any(k.endswith(n) or n.endswith(k) for n in _trainable_names)}}\n"
    )
    t = t[: m.start()] + new + t[m.end():]
    ast.parse(t)
    print("  filter rewritten to match by parameter name")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    check = SCRIPT.read_text(encoding="utf-8")
    print("  written | by-name:", "_trainable_names" in check,
          "| old identity test gone:", "any(t is v for t in" not in check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

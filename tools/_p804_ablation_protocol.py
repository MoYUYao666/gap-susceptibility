# -*- coding: utf-8 -*-
r"""Read Paper A's original rank-ablation protocol so the rerun matches it.

The rerun is only informative if it reproduces the paper's own setting: the same sample cap, epochs
and alpha rule. This extracts that protocol from the paper and from the archived run scripts.

    python tools/_p804_ablation_protocol.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=" * 104)
    print("Paper A's stated protocol")
    print("=" * 104)
    for f in sorted((REPO / "paper合" / "sections").glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"[^.\n]{0,150}(?:5000|5\{,\}000|\$5000|10 epochs|alpha\s*=\s*2r|"
                             r"\\\\alpha=2r|learning rate|batch size)[^.\n]{0,220}", t):
            seg = " ".join(m.group(0).split())
            if len(seg) > 50:
                ln = t[:m.start()].count("\n") + 1
                print(f"  [{f.name}:{ln}] {seg[:280]}")

    print()
    print("=" * 104)
    print("archived scripts that produced the LoRA sweeps")
    print("=" * 104)
    for rel in ("experiments/main.py", "experiments/phase1_experiments.py",
                "experiments/seed_experiments.py", "experiments/theory/v1_rank_sweep.py",
                "experiments/theory/adapter_sweep.py", "experiments/download_data.py"):
        p = REPO / rel
        if not p.exists():
            print(f"  {rel}: absent")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  --- {rel} ---")
        for m in re.finditer(r"(?:^|\n)\s*(?:SEEDS|BATCH|EPOCHS|LR|MAX_SAMPLES|RANKS|CONFIGS)"
                             r"[^\n]{0,120}", t):
            print(f"     {m.group(0).strip()[:120]}")
        for m in re.finditer(r"[^\n]{0,60}alpha\s*=\s*[^\n,)]{0,40}", t):
            s = m.group(0).strip()
            if "alpha" in s and ("2 *" in s or "2*" in s or "r" in s):
                print(f"     alpha: {s[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

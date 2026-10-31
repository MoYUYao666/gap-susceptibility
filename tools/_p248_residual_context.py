# -*- coding: utf-8 -*-
r"""看 `paper合` 里 `+0.079` 与 `Visual Fragility` 的上下文（2026-10-12）。

    python tools\_p248_residual_context.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FH = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
    sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))


def show(pat: str, label: str, w: int = 420, n: int = 10):
    print("=" * 96)
    print(f"「{label}」")
    print("=" * 96)
    total = 0
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(pat, t, re.I):
            total += 1
            if total > n:
                continue
            ln = t[:m.start()].count("\n") + 1
            s = " ".join(t[max(0, m.start() - w // 2):m.start() + w].split())
            print(f"\n  [{Path(f).name}:{ln}]")
            print(f"    …{s[:460]}…")
    print(f"\n  共 {total} 处\n")


def main() -> int:
    show(r"\+0\.079", "+0.079")
    show(r"Visual Fragility", "Visual Fragility", w=360, n=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

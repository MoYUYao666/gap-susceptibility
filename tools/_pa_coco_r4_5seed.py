# -*- coding: utf-8 -*-
r"""把 COCO r4 换成新的 5-seed 值（$-0.0414$ → $-0.0430$）（2026-10-11）。

## 依据（`outputs/coco_sweep_text_only/r4/text_only/seed*/results.json`）

逐 seed：$-0.0438$ / $-0.0402$ / $-0.0431$ / $-0.0408$ / $-0.0472$
→ **mean $= -0.043013$，sd $= 0.002777$**（n=5，batch 128）

**旧值**（`coco_sweep/r4/text_only`，3 seed）：$-0.0414 \pm 0.0015$

**翻转结论不变**：Flickr30k `text_only`（$-0.0304$）> `both`（$-0.0204$）；
COCO `both`（$-0.0886$）> `text_only`（$-0.0430$）。

    python tools\_pa_coco_r4_5seed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

PAIRS = [
    (r"text-only gives $-0.0414\pm0.0015$ and both-position $-0.0886\pm0.0026$",
     r"text-only gives $-0.0430\pm0.0028$ and both-position $-0.0886\pm0.0026$"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n_ok = 0
    for old, new in PAIRS:
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠️'} 命中 {c}: {old[:60]}…")
        if c == 1:
            t = t.replace(old, new, 1)
            n_ok += 1
    print(f"  → {n_ok}/{len(PAIRS)}")

    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    assert r"$-0.0430\pm0.0028$" in t2, "新值未写入"
    assert r"$-0.0414\pm0.0015$" not in t2, "旧值仍在"
    print("  ✅ COCO r4 已换为 5-seed 值")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

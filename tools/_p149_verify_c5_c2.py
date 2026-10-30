# -*- coding: utf-8 -*-
r"""核实 C5（4-bit/bf16）与 C2（seed 数）的真实状态（2026-10-10）。

## 疑点

1. 风险清单说"4-bit 与 bf16 的差异**未量化**"，但补充材料里**搜不到 '4-bit'** →
   该说明到底写没写进去？
2. 风险清单说"CLIP B/32 为 **5** seed；其余新增为 1 seed"，
   而 `tools/_p138` 实测三骨干**各 3 seed** → 清单过期？

    python tools\_p149_verify_c5_c2.py
"""
from __future__ import annotations

import glob
import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=" * 72)
    print("① C5：4-bit / bf16 在论文与归档里的痕迹")
    print("=" * 72)
    pats = ["4-bit", "4bit", "bf16", "bfloat16", "quantis", "quantiz", "QLoRA"]
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = {p: t.lower().count(p.lower()) for p in pats}
        hits = {k: v for k, v in hits.items() if v}
        if hits:
            print(f"  {Path(f).name:<18} {hits}")
    print("\n  归档里的 4bit 产物：")
    for d in ("outputs/vlm_strictfreeze", "outputs/vlm_strictfreeze/4bit"):
        p = REPO / d
        if p.exists():
            print(f"    {d}:")
            for x in sorted(p.glob("*.json")):
                print(f"      {x.name}  {x.stat().st_size} B")

    print()
    print("=" * 72)
    print("② C2：严格冻结的 seed 覆盖（实测）")
    print("=" * 72)
    for label, root in (("CLIP B/32 r4", "outputs/strict_freeze_b32_r4"),
                        ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4"),
                        ("OpenCLIP r4", "outputs/strict_freeze_oclip/r4"),
                        ("CLIP B/32 r8（旧）", "outputs/strict_freeze_b32_r8")):
        p = REPO / root
        if not p.exists():
            continue
        for arm in ("text_only", "both", "vision_only"):
            seeds = sorted(x.name for x in (p / arm).glob("seed*")) if (p / arm).exists() else []
            if seeds:
                print(f"  {label:<20} {arm:<12} {len(seeds)} seed  {seeds}")
    print("\n  论文里关于 seed 的陈述：")
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"[^.]{0,150}(five|three|5|3)[- ]seed[^.]{0,150}\.", t, re.I):
            s = " ".join(m.group(0).split())
            print(f"    [{Path(f).name}] {s[:190]}")

    print()
    print("=" * 72)
    print("③ 风险清单的 B/C 表整表（判哪些行是旧的结论）")
    print("=" * 72)
    f = REPO / "docs" / "PAPERA_REVIEWER_RISKS.md"
    t = io.open(f, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\|\s*\*\*(B\d|C\d)\*\*\s*\|([^|]*)\|([^|]*)\|([^|]*)\|", t):
        print(f"  {m.group(1):<4} | {m.group(2).strip()[:52]:<52} | "
              f"{m.group(3).strip()[:38]:<38} | {m.group(4).strip()[:30]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

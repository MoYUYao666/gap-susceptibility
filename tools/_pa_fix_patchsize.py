# -*- coding: utf-8 -*-
r"""修 `empirical.tex` 里 patch-size 的旧归因（与表注一致）（2026-10-11）。

## 原文

> *"The measurements above show that the ordering is a property not of vision-language adaptation
> in general but of **the patch size the encoder uses**, and Section~\ref{sec:theory} derives the
> mechanism that produces it."*

## 为什么错

论文**表注**（已修正）写 *"Patch size **does not separate** the groups"*，
且正文另有一段明写 *"That reading does not survive the matched comparison: CLIP B/16 and CLIP B/32,
measured at the same rank under the same protocol, order the arms identically despite differing in
patch size by a factor of two"*、*"We therefore report the grouping as a regularity over seven
configurations **rather than as a property of patch size**"*。

→ **上面那句是与三处都矛盾的旧归因残留。**

## 改为

按**预训练目标**分组（对比式 image--text 预训练 vs 其它目标），这正是表注与正文的现行口径。

    python tools\_pa_fix_patchsize.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

PAT = re.compile(
    r"The measurements above show that the ordering is a\s+property not of vision-language "
    r"adaptation in general but of the patch size the encoder uses, and\s+"
    r"Section~\\ref\{sec:theory\} derives the mechanism that produces it\.")
NEW = (r"The measurements above show that the ordering follows the pre-training objective rather "
       r"than vision-language adaptation in general: every contrastively pre-trained backbone, at "
       r"either patch size, puts text-only at the smallest gap change, while the two backbones "
       r"trained with other objectives put both positions there. Section~\ref{sec:theory} derives "
       r"the mechanism that produces it.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    ms = list(PAT.finditer(t))
    print(f"=== 正则命中 {len(ms)} ===")
    if len(ms) != 1:
        for m in ms:
            print("   " + repr(t[max(0, m.start() - 80):m.end() + 80]))
        return 1
    t2 = PAT.sub(lambda _: NEW, t, count=1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_patchsize")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    assert "but of the patch size the encoder uses" not in t3, "旧归因仍在"
    assert "follows the pre-training objective" in t3, "新表述未写入"
    print("  ✅ 已改为「按预训练目标分组」，与表注/正文一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

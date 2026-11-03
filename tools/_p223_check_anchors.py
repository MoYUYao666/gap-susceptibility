# -*- coding: utf-8 -*-
r"""核 `_p222` 的锚点是否逐字命中（2026-10-12）。

    python tools\_p223_check_anchors.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    t = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    print("=" * 88)
    print("① 标题原文（repr，看空格）")
    print("=" * 88)
    m = re.search(r"\\title\{(.*?)\}", t, re.S)
    print("  repr:", repr(m.group(0)))

    print()
    print("=" * 88)
    print("② 各锚点逐字检查")
    print("=" * 88)
    ANCH = {
        "标题": r"\title{Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning:  Why the Modality Gap Is Not a Universal Health Metric}",
        "four decimals": "matches measurement to four decimals",
        "governs": "Only the second governs zero-shot accuracy, and it is free to monitor: ",
        "legacy free": ("it is free to monitor: the Kendall order-preservation coefficient "
                        "$\\tau$ follows from the top-$k$ class sets a validation pass "
                        "already produces."),
        "monitor 句": ("Two practical points follow: $\\tau$ is an earlier and more sensitive "
                       "indicator of order erosion than top-1 itself, and it is computable from "
                       "the top-$k$ class sets already available during validation---making it a "
                       "zero-overhead training-time monitor for classification-oriented "
                       "fine-tuning."),
    }
    for k, v in ANCH.items():
        c = t.count(v)
        print(f"  {'✅' if c == 1 else ('⚠️ ' if c > 1 else '🔴')} {k:<14} 命中 {c}")
        if c == 0:
            # 打印最接近的片段
            key = v[:40]
            i = t.find(key)
            if i >= 0:
                print(f"       最接近: {repr(t[i:i + len(v) + 40])[:180]}")
            else:
                print(f"       连前 40 字符都找不到: {repr(key)}")

    print()
    print("=" * 88)
    print("③ highlights.tex 锚点")
    print("=" * 88)
    h = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    for ln in h.splitlines():
        if "1.000" in ln:
            print("  repr:", repr(ln))

    print()
    print("=" * 88)
    print("④ main.tex 的 abstract 与 Discussion 锚点")
    print("=" * 88)
    print(f"  \\begin{{abstract}}: {t.count(chr(92) + 'begin{abstract}')}")
    print(f"  \\section{{Discussion}}: {t.count(chr(92) + 'section{Discussion}')}")
    print(f"  sec:epoch_sweep 已存在: {'sec:epoch_sweep' in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

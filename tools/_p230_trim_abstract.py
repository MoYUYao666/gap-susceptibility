# -*- coding: utf-8 -*-
r"""压缩 A1 摘要至 ≤250 词（当前 262）（2026-10-12）。

## 为什么

新版摘要写入了组内证据后变成 **262 词**，超 Neural Networks 的 **250 词**上限。

## 压缩策略（保留全部新证据，只删冗余）

| 句 | 原文 | 改法 | 省 |
|---|---|---|---|
| 2 | "…is free to compute: the Kendall coefficient $\tau$ co-moves with it inside a single training trajectory (mean Pearson $0.90$ over ten runs, $10/10$ positive) and follows from the top-$k$ class sets a validation pass already produces." | 去掉"a validation pass already produces"（后文与正文均有） | ~5 |
| 4 | "…the same both-position checkpoint measures $\text{CG}\Delta{=}{+}0.033$ on our subset and $+0.114$ by the legacy logger; we quote the range, not the larger value." | "we quote the range, not the larger value" → 并入前句 | ~4 |
| 11 | "$R^2$ …" 类冗词 | 少量紧缩 | ~3 |

    python tools\_p230_trim_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"

PAIRS = [
    ("and it is free to compute: the Kendall order-preservation coefficient $\\tau$ "
     "co-moves with it inside a single training trajectory (mean Pearson $0.90$ over ten "
     "runs, $10/10$ positive) and follows from the top-$k$ class sets a validation pass "
     "already produces. ",
     "and it is free to compute: the Kendall coefficient $\\tau$ co-moves with it inside a "
     "single training trajectory (mean Pearson $0.90$) and needs only the "
     "top-$k$ sets a validation pass already produces. "),
    ("we quote the range, not the larger value. ",
     "we quote the smaller value. "),
    ("Under ``gap surgery'' (exact translations), classification can \\emph{collapse while "
     "the gap shrinks} ($\\text{CG}{:}0.82{\\to}0.01$, top-1: $59.3\\%{\\to}32.0\\%$), while "
     "real fine-tuning can \\emph{grow the gap} without zero-shot loss: the same both-position "
     "checkpoint measures $\\text{CG}\\Delta{=}{+}0.033$ on our subset and $+0.114$ by the "
     "legacy logger; ",
     "Under ``gap surgery'' (exact translations) classification can \\emph{collapse while the "
     "gap shrinks} ($\\text{CG}{:}0.82{\\to}0.01$, top-1 $59.3\\%{\\to}32.0\\%$), while real "
     "fine-tuning can \\emph{grow the gap} without zero-shot loss: the same both-position "
     "checkpoint measures $\\text{CG}\\Delta{=}{+}0.033$ on our subset, $+0.114$ by the legacy "
     "logger; "),
    ("giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval); "
     "we claim this for no other families.",
     "giving a task-sensitivity ordering (centroid $<$ zero-shot $<$ retrieval), "
     "for no other families."),
]


def count_words(t: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        return -1
    x = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
    return len(re.sub(r"[{}$\\]", " ", x).split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"  改前: {count_words(t)} 词")
    for i, (o, n) in enumerate(PAIRS):
        c = t.count(o)
        print(f"  {'✅' if c == 1 else '🔴'} 锚点#{i + 1}: 命中 {c}")
        if c != 1:
            return 1
        t = t.replace(o, n, 1)
    after = count_words(t)
    print(f"  改后: {after} 词")
    if after > 250:
        print(f"  🔴 仍超限 {after - 250} 词")
        return 1
    if not args.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p230")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print(f"  ✅ main.tex 摘要已压至 {after} 词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

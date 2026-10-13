# -*- coding: utf-8 -*-
r"""核实审稿人 3 的三条指控 + 我自己加的检查（2026-10-12）。

| # | 指控 | 核实方法 |
|---|---|---|
| A | `abstract.tex` 是半成品（新标题 + 旧摘要，从不提 monitor） | 读该文件的 title 与 abstract，查是否含 "monitor" |
| B | `main_zh.tex` 仍带旧标题 | 读其 title |
| C | `docs/A1_VENUE_DECISION.md` 仍写"在 Neurocomputing 在审" | 搜该文件 |
| D | 论文说 "a fixed tau<0.5 threshold fires at lambda=-0.5 for every k>=5" | 读该段 |
| E | 论文说 tau "orders datasets, not individual runs"（seed 内 rho=-0.5/-0.5/+1.0） | 读该段 |

    python tools\_p203_verify_reviewer3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
OUT = REPO / "outputs" / "analysis" / "a1_reviewer3_verify.json"


def show(label: str, text: str, pat: str, w: int = 320, n: int = 2):
    ms = list(re.finditer(pat, text, re.S | re.I))
    print(f"\n  ── {label}（命中 {len(ms)}）──")
    for m in ms[:n]:
        s = " ".join(text[max(0, m.start() - 180):m.start() + w].split())
        print(f"     …{s[:460]}…")
    return len(ms)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    print("=" * 88)
    print("A. abstract.tex 是否半成品")
    print("=" * 88)
    ab = io.open(A1 / "abstract.tex", encoding="utf-8", errors="replace").read()
    mt = re.search(r"\\title\{(.*?)\}\s*\n", ab, re.S)
    ma = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", ab, re.S)
    title = " ".join(mt.group(1).split()) if mt else "(无)"
    body = " ".join(ma.group(1).split()) if ma else "(无)"
    print(f"  title: {title[:120]}")
    print(f"  摘要首 200 字符: {body[:200]}")
    print(f"  含 'monitor': {'✅ 是' if 'monitor' in body.lower() else '🔴 否'}")
    print(f"  含 'zero-overhead': {'✅ 是' if 'zero-overhead' in body.lower() else '🔴 否'}")
    res["abstract_has_monitor"] = "monitor" in body.lower()
    res["abstract_title"] = title

    print()
    print("=" * 88)
    print("B. main_zh.tex 的标题")
    print("=" * 88)
    zh = A1 / "main_zh.tex"
    if zh.exists():
        t = io.open(zh, encoding="utf-8", errors="replace").read()
        m = re.search(r"\\title\{(.*?)\}\s*\n", t, re.S)
        print("  " + (" ".join(m.group(1).split())[:140] if m else "(无 title)"))
        res["main_zh_title"] = " ".join(m.group(1).split())[:140] if m else None
    else:
        print("  （无 main_zh.tex）")

    print()
    print("=" * 88)
    print("C. docs/A1_VENUE_DECISION.md 的投稿状态陈述")
    print("=" * 88)
    vd = REPO / "docs" / "A1_VENUE_DECISION.md"
    if vd.exists():
        t = io.open(vd, encoding="utf-8", errors="replace").read()
        for pat in (r"NEUCOM-D-26-20952", r"Submitted to Journal", r"under review"):
            n = show(pat, t, pat, w=260, n=2)
            res[f"venue_decision_{pat}"] = n

    print()
    print("=" * 88)
    print("D/E. 论文里 τ 阈值与「orders datasets, not runs」的原文")
    print("=" * 88)
    main = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    show("τ<0.5 阈值", main, r"fixed \$\?\\tau|threshold.{0,60}0\.5|0\.5.{0,80}separates neither")
    show("orders datasets", main, r"orders datasets|not individual runs")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

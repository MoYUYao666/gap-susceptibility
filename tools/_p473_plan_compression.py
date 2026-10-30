# -*- coding: utf-8 -*-
r"""量化 P3 的压缩规模，并制定"哪些移入 Supplementary"的方案（2026-10-13）。

## 官方规定（`docs/guides/_prl_guide.txt`，穷举确认）

- **Mandatory Submission Requirements 第 1 条**：**双栏 + ≤7 页**，**含全部材料**（narrative/figures/tables/references）
- **Guide 鼓励 Supplementary material**，并要求在正文引用
- **LaTeX 允许双栏**；Word 必须单栏

## 现状

`paper3/paper_ieee/main.tex` = `\documentclass[journal]{IEEEtran}`，**14 页**（投稿时 11 页）。
`[journal]` 选项下 IEEEtran 正文为**双栏**，与 PRL 要求的"double column"同类。

**⇒ 需从 14 页压到 ≤7 页**（约减半）。本脚本量化各节的字符量，给出"移出/精简"方案。

    python tools\_p473_plan_compression.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper3" / "paper_ieee" / "sections"
OUT = REPO / "outputs" / "analysis" / "p3_compression_plan.json"


def count_words(tex: str) -> int:
    """粗估正文词数：去命令、去数学、计英文词。"""
    t = re.sub(r"\\begin\{(table|figure|tabular|algorithm|equation|align|split)\*?\}.*?\\end\{\1\*?\}",
               " ", tex, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " X ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", t)
    t = re.sub(r"[^A-Za-z][^A-Za-z]+", " ", t)
    return len([w for w in t.split() if len(w) > 1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {"sections": {}}

    print("=" * 104)
    print("各节的字符量与粗估词数")
    print("=" * 104)
    print(f"  {'节':<26} {'字符':>8} {'粗估词数':>9} {'表格':>5} {'图':>4} {'公式':>5}")
    tot_c = tot_w = 0
    for f in sorted(SEC.glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        c = len(t)
        w = count_words(t)
        nt = len(re.findall(r"\\begin\{table", t))
        nf = len(re.findall(r"\\begin\{figure", t))
        ne = len(re.findall(r"\\begin\{(equation|align)", t))
        tot_c += c
        tot_w += w
        print(f"  {f.stem:<26} {c:>8,} {w:>9,} {nt:>5} {nf:>4} {ne:>5}")
        rep["sections"][f.stem] = {"chars": c, "words": w, "tables": nt, "figures": nf, "equations": ne}
    print(f"  {'合计':<26} {tot_c:>8,} {tot_w:>9,}")
    rep["total_chars"] = tot_c
    rep["total_words"] = tot_w

    print()
    print("=" * 104)
    print("当前 PDF 页数")
    print("=" * 104)
    pdf = REPO / "paper3" / "paper_ieee" / "main.pdf"
    pages = None
    if pdf.exists():
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, encoding="utf-8", errors="replace")
        for ln in (r.stdout or "").splitlines():
            if ln.startswith("Pages:"):
                pages = int(ln.split(":", 1)[1].strip())
        print(f"  main.pdf = {pages} 页（IEEEtran [journal]，双栏正文）")
    rep["pages_now"] = pages

    print()
    print("=" * 104)
    print("压缩方案（按\u300c移出优先\u300d排序）")
    print("=" * 104)
    plan = [
        ("appendix", "整节移入 Supplementary（理论推导细节、误差界、逐块 Γ 计算）",
         "Guide 鼓励补充材料；审稿人点名要的多是**结论与表**，推导可外置"),
        ("experiments", "保留主表与结论；把**逐 run 表、分辨率曲线、E0 预算曲线、功效算式**移出",
         "R3.12 要的逐块 Γ/rank 表可在正文保留精简版，完整版进补充"),
        ("theory", "保留定理与 Corollary 陈述；**证明移入补充**",
         "R1.5/R3.3 关心的是**证明是否成立**，可在正文给关键 Lemma，完整证明进补充"),
        ("related_work", "压缩为 1 段 + 与先前工作的差异",
         "R2.2 要求的是**明确差异**，不需要长综述"),
        ("introduction", "压缩贡献列表；去掉重复的动机段", "标准压缩"),
        ("discussion", "合并 limitation 条目；把 12 条限制编成表", "表格化最省版面"),
        ("conclusion", "压缩至 1 段", "标准压缩"),
    ]
    for name, action, why in plan:
        m = rep["sections"].get(name, {})
        print(f"  ── {name}（{m.get('chars', 0):,} 字符 / {m.get('words', 0):,} 词）")
        print(f"      {action}")
        print(f"      理由：{why}")
        print()
    rep["plan"] = [{"section": n, "action": a, "why": w} for n, a, w in plan]

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""诊断 A1 的"significance 不足"：**contributions 的呈现顺序**（2026-10-10）。

## 假设（须验证，不猜）

编辑说 *"falls within the aim and scope … did not meet the significance level"*。
**A1 的 Discussion 已写明"划出适用边界"，但**Introduction 的第一句是**否定式**：
> *"The modality gap is not a universal health metric"*

**→ 若 Introduction 的 contributions 列表把"否定/边界"放在第一位、而把"τ 是更有信息的信号"
与"闭式分析"放后面，则审稿人读到的是"一篇纠错文章"，
而不是"一篇给出更好指标的文章"——这可以直接解释 significance 评价。**

## 本脚本

抽取 Introduction 的**逐句**与 contributions 列表，统计：
- 否定式表述（not / fails / does not / dispute）出现位置；
- 正面表述（we show / we provide / τ predicts）出现位置。

    python tools\_p91_a1_positioning.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"
OUT = REPO / "outputs" / "analysis" / "a1_positioning.json"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    m = re.search(r"\\section\{Introduction\}(.*?)\\section\{Setup\}", t, re.S)
    if not m:
        print("  ❌ 未找到 Introduction")
        return 1
    intro = m.group(1)
    plain = " ".join(re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", intro).split())
    sents = re.split(r"(?<=[.!?])\s+", plain)

    print(f"=== Introduction 共 {len(sents)} 句 ===")
    NEG = re.compile(r"\b(not|fails?|does not|do not|dispute|unconditional|cannot|neither)\b", re.I)
    POS = re.compile(r"\b(we show|we provide|we introduce|we find|predicts|governs|"
                     r"delineate|identify|the more informative)\b", re.I)
    neg_i, pos_i = [], []
    for i, s in enumerate(sents):
        tag = []
        if NEG.search(s):
            tag.append("NEG")
            neg_i.append(i)
        if POS.search(s):
            tag.append("POS")
            pos_i.append(i)
        if tag:
            print(f"  [{i:>2}] {'/'.join(tag):<7} {s[:150]}")

    print("\n=== 统计 ===")
    print(f"  否定式句：{len(neg_i)} 句 ｜ 首次出现在第 {neg_i[0] if neg_i else '-'} 句")
    print(f"  正面式句：{len(pos_i)} 句 ｜ 首次出现在第 {pos_i[0] if pos_i else '-'} 句")
    if neg_i and pos_i:
        if pos_i[0] < neg_i[0]:
            print("  → ✅ **正面表述更早**（读者先看到贡献）")
        else:
            print(f"  → ⚠️ **否定式更早**（第 {neg_i[0]} 句 vs 第 {pos_i[0]} 句）"
                  f" —— 读者先看到「这不是什么」，再看「这是什么」")
    print("\n=== contributions 列表（若有）===")
    for mm in re.finditer(r"\\begin\{itemize\}(.*?)\\end\{itemize\}", intro, re.S):
        for it in re.finditer(r"\\item\s+(.*?)(?=\\item|$)", mm.group(1), re.S):
            s = " ".join(it.group(1).split())[:200]
            print("  •", s)

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            __import__("json").dumps({
                "n_sentences": len(sents), "neg_first": neg_i[0] if neg_i else None,
                "pos_first": pos_i[0] if pos_i else None,
                "neg_count": len(neg_i), "pos_count": len(pos_i),
            }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

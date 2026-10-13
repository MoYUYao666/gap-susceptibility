# -*- coding: utf-8 -*-
r"""为"8 页 → 7 页"给出可执行的精简选项（不擅自删，只列清单与可省行数）。

页数账（实测，`tools/_measure_prl_layout.py`）：
  前置块 1 页（cas-dc 把摘要/highlights 排成通栏） + 正文 5 页 + 参考文献 2 页 = 8 页
  上限 7 页 → 需省出约 1 页 ≈ 正文 200 词 或 参考文献 10 条 或"图表降为单栏"

    python tools/_plan_prl_trim.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
MD = OUT / "MANUSCRIPT.md"
REFS = OUT / "_refs_used.json"


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    refs = json.loads(REFS.read_text(encoding="utf-8"))

    print("=" * 74)
    print("方案 A：删冗余引用（每条省约 2 行 ≈ 0.04 页）")
    print("=" * 74)
    # 找"同一用途出现多次"的引用簇
    clusters = {
        "PEFT 综述（4 篇用于同一处）": ["xu2026peftsurvey", "xin2024vpeftsurvey", "prottasha2025pefta2z",
                                "lialin2023scalingdown", "jin2024efficientmllm", "shao2025tokencompression"],
        "token/效率相关（与本文主线较远）": ["shao2025tokencompression", "li2025tokenpacker"],
        "量化类（QLoRA 已代表该点）": ["dettmers2023qlora", "jiang2024mora"],
        "提示类（保留 2 篇即可）": ["li2021prefixtuning", "lester2021prompttuning", "khattak2023maple",
                          "qiu2024progressive", "mao2022unipelt"],
        "视觉适配（保留 3 篇即可）": ["jia2022vpt", "lian2022ssf", "chen2022adaptformer", "jie2022convpass",
                           "he2023safe"],
        "基准/污染（保留最相关 2 篇）": ["fu2025mme", "song2025bothleaked", "chen2024rightway"],
    }
    for name, ks in clusters.items():
        present = [k for k in ks if any(r["key"] == k for r in refs)]
        if len(present) > 1:
            print(f"\n  {name}")
            for k in present:
                e = next(r for r in refs if r["key"] == k)
                print(f"     - {k:<30} {(e['title'] or '')[:52]}")

    print("\n" + "=" * 74)
    print("方案 B：正文精简（每 200 词 ≈ 0.2 页；当前正文约 3,790 词）")
    print("=" * 74)
    body = md.split("## 1. Introduction", 1)[-1]
    for sec in re.split(r"\n(?=### |## )", body):
        head = sec.split("\n", 1)[0].replace("## ", "").replace("### ", "")[:48]
        txt = " ".join(l for l in sec.splitlines() if l.strip() and not l.startswith(("|", "**Table")))
        n = len([w for w in re.split(r"\s+", txt) if re.search(r"[A-Za-z]", w)])
        if n > 120:
            print(f"  {head:<50} {n:>4} 词")

    print("\n" + "=" * 74)
    print("方案 C：图表降为单栏（可省约 0.3 页）")
    print("=" * 74)
    tex = (OUT / "main_prl.tex").read_text(encoding="utf-8")
    print(f"  table* 数: {tex.count('begin{table*}')} ｜ figure* 数: {tex.count('begin{figure*}')}")
    print("  把 1 个 table* 与 figure* 改为单栏（table/figure），每项约省 0.15–0.25 页")

    print("\n" + "=" * 74)
    print("推荐组合（可达 7 页，且不削弱主线）")
    print("=" * 74)
    print("  1) 删 xin2024vpeftsurvey、prottasha2025pefta2z 两篇同用途综述  （−2 条）")
    print("  2) 删 qiu2024progressive、mao2022unipelt 两篇同族提示/统一框架（−2 条）")
    print("  3) 正文 §2.1/§2.2 各压缩一处分点陈述                        （−200 词）")
    print("  → 合计约省 0.55 页；如仍差，再把 figure* 改单栏（−0.2 页）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

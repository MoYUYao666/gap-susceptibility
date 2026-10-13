# -*- coding: utf-8 -*-
r"""第五轮：从 8 页压回 7 页，同时保住引用密度（目标 45 条上下）。

诊断：`_measure_prl_layout.py` 显示第 8 页仅溢出约 130 词（参考文献尾巴）。
手段（先引用瘦身，后正文压缩——优先保留引用数）：
  A. 三处"同一论点挂 3 篇"的引用减到 1–2 篇（同行评审最不介意这种精简）
  B. 正文压缩若干处冗语

    python tools/_fit_round5.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

EDITS: list[tuple[str, str]] = [
    # A. 引用瘦身：3 篇 → 1 篇（该论点不需要三篇支撑）
    ("[qiu2025lowprecision; golden2024flashattentionstable; budzinskiy2025numerical]",
     "[qiu2025lowprecision]"),
    ("[bouthillier2021variance; d2020underspecification;\ndror2018significance]",
     "[bouthillier2021variance; d2020underspecification]"),
    ("[dettmers2023qlora; jiang2024mora; hayou2024loraphus; kalajdzievski2023rslora]",
     "[dettmers2023qlora; jiang2024mora]"),
    ("[chen2022adaptformer; jie2022convpass; he2023safe; gao2024clipadapter]",
     "[chen2022adaptformer; jie2022convpass; gao2024clipadapter]"),
    ("[zhang2023adalora; wang2024loraga; silvarodriguez2024closerlook; zanella2024cliplora]",
     "[zhang2023adalora; wang2024loraga; zanella2024cliplora]"),

    # B. 正文压缩（等价改写）
    ("The first decision is *where* adaptive capacity should be placed. A multimodal model contains at\n"
     "least three qualitatively different sites: a visual encoder pretrained on images, a projector that\n"
     "translates visual features into the language model's space, and a language backbone pretrained on\n"
     "text. These sites differ in what they compute, in how many parameters they contain, and in the\n"
     "consequences of modifying them.",
     "The first decision is *where* adaptive capacity is placed. A multimodal model contains at least three\n"
     "qualitatively different sites: a visual encoder pretrained on images, a projector translating visual\n"
     "features into the language model's space, and a language backbone pretrained on text. They differ in\n"
     "what they compute, how many parameters they hold, and what modifying them costs."),
    ("Our contribution is\nthreefold. First, I state the two decisions separately and show why conflation is the source of the\n"
     "difficulty (§2). Second, I set out, with concrete instances, what the published evidence does and\n"
     "does not support (§3); each instance is verifiable against the cited source. Third, I give a\n"
     "twelve-item reporting checklist intended to make future results comparable, and therefore citable\n"
     "(§4). I close with what I take to be the field's most useful next step (§5).",
     "The contribution is threefold: the two decisions are stated separately and conflation identified as\n"
     "the source of the difficulty (§2); the evidence is examined through concrete instances, each\n"
     "verifiable against its source (§3); and a twelve-item reporting checklist is given to make future\n"
     "results comparable and therefore citable (§4)."),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    n = 0
    for old, new in EDITS:
        if old in t:
            t = t.replace(old, new, 1); n += 1
        else:
            print(f"  ⚠ 未命中: {old[:56]}…")
    keys = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", t):
        if "://" in m.group(1):
            continue
        for part in re.split(r"[;,]", m.group(1)):
            k = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", k):
                keys.add(k)
    print(f"\n命中 {n}/{len(EDITS)} 处 ｜ 唯一 key {len(keys)} 条")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

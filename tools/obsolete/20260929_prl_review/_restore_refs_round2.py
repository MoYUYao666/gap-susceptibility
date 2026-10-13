# -*- coding: utf-8 -*-
r"""第二轮：把剩余引用补入正文，并同步加强正文瘦身，以守住 PRL 的 7 页上限。

依据：`tools/_benchmark_prl_reviews.py` 实测同类综述参考文献中位 55、四分位 37–59。

    python tools/_restore_refs_round2.py            # 预演
    python tools/_restore_refs_round2.py --apply
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

EDITS: list[tuple[str, str]] = [
    # 综述定位：语言侧 + 视觉侧 + 效率类三篇
    ("tabulating reported results; two cover the language and vision settings respectively [xu2026peftsurvey], and others survey efficiency more broadly [jin2024efficientmllm].",
     "tabulating reported results; two cover the language [xu2026peftsurvey] and vision [xin2024vpeftsurvey]\nsettings, and others survey efficiency more broadly [jin2024efficientmllm; shao2025tokencompression;\nlialin2023scalingdown]."),
    # 提示族：补 Progressive（多模态提示的递进式设计）
    ("[li2021prefixtuning; lester2021prompttuning; khattak2023maple].",
     "[li2021prefixtuning; lester2021prompttuning; khattak2023maple; qiu2024progressive]."),
    # 统一框架：补 UniPELT
    ("have only recently begun to appear [belanec2026peftbench].",
     "have only recently begun to appear [belanec2026peftbench; mao2022unipelt]."),
    # 预算构成：把"秩 + 精度"这一分配轴要点写出来（QLoRA 的实质贡献）
    ("Equal counts are not equal capacity, because where the parameters sit matters:",
     "The budget itself is composite: low-rank adaptation trades rank against numerical precision\n[dettmers2023qlora], so two papers can report the same parameter count while spending it on different\nthings. Even at equal counts, where the parameters sit matters:"),
]

# 加强瘦身，为上述新增腾出行数
TRIMS: list[tuple[str, str]] = [
    ("Its leverage is disproportionate to its size, which also makes it a bottleneck: improvements there cannot\nrecover information the encoder never encoded.",
     "Its leverage is disproportionate to its size, and that also makes it a bottleneck: improvements there\ncannot recover information the encoder never encoded."),
    ("*Structure-driven allocation* computes the score from the frozen model rather than from training, which makes the allocation predictively usable before training.",
     "*Structure-driven allocation* computes the score from the frozen model rather than from training, making\nthe allocation usable before training."),
    ("The distinction changes the direction of the conclusion: a configuration that fails for an implementation reason is not a\nmethod that fails.",
     "The distinction changes the conclusion's direction: a configuration that fails for an implementation\nreason is not a method that fails."),
    ("and the purpose of stating it here is to make the requirement citable.",
     "and stating it makes the requirement citable."),
    ("The consequence for the field's direction is, we think, straightforward. Another adapter variant\nevaluated under an unstated protocol adds little to a body of evidence that is already difficult to\nassemble.",
     "The consequence for the field's direction is straightforward. Another adapter variant evaluated under an\nunstated protocol adds little to a body of evidence already difficult to assemble."),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    na = nt = 0
    for old, new in EDITS:
        if old in t:
            t = t.replace(old, new, 1); na += 1
        else:
            print(f"  ⚠ 补引用未命中: {old[:56]}…")
    for old, new in TRIMS:
        if old in t:
            t = t.replace(old, new, 1); nt += 1
        else:
            print(f"  ⚠ 瘦身未命中: {old[:56]}…")

    keys = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", t):
        if "://" in m.group(1):
            continue
        for part in re.split(r"[;,]", m.group(1)):
            k = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", k):
                keys.add(k)
    print(f"\n补引用 {na}/{len(EDITS)} ｜ 瘦身 {nt}/{len(TRIMS)} ｜ 唯一 key {len(keys)} 条")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

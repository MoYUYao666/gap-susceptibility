# -*- coding: utf-8 -*-
r"""定位 `paper合` 里的内部矛盾与硬错（2026-10-12）。

| 项 | 内容 |
|---|---|
| C1 | 架构计数：five / six / seven 三种说法 |
| C2 | `α is universally negative` 与归档矛盾 |
| C3 | `+0.079` 张冠李戴 |
| C4 | isotropic Gaussian noise 与代码不符 |
| C5 | 55 vs 49 run 计数 |
| C6 | discussion.tex:56 的 pre-hoc 承诺与 limitation 冲突 |
| C7 | COCO/BLIP-1 未披露 |

    python tools\_p275_locate_contradictions.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FH = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
    sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))

ITEMS = [
    ("C1 架构计数", r"(five|six|seven|six|5|6|7)\s+(architectures|backbones|configurations)|"
                    r"(architectures|backbones)"),
    ("C2 α 普适负", r"universally negative|consistently negative"),
    ("C3 +0.079", r"\+0\.079"),
    ("C4 isotropic", r"isotropic"),
    ("C5 55/49", r"\b55\b|\b49\b|\b43\b"),
    ("C6 pre-hoc", r"pre-hoc|without training"),
    ("C7 COCO/BLIP 披露", r"test_dataset|chance level|near-random"),
]


def main() -> int:
    for label, pat in ITEMS:
        print("=" * 96)
        print(label)
        print("=" * 96)
        tot = 0
        for f in FH:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            for m in re.finditer(pat, t, re.I):
                tot += 1
                if tot > 14:
                    continue
                ln = t[:m.start()].count("\n") + 1
                s = " ".join(t[max(0, m.start() - 170):m.start() + 220].split())
                print(f"  [{Path(f).name}:{ln}] …{s[:380]}…")
        print(f"  共 {tot} 处\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""结论措辞：predicts → reproduces（2026-10-07）。

理由：$\alpha$、$\beta$ 是**逐 run 拟合**的，故此处的 R² 衡量"**函数形式是否足够**"，
而非"能否事先算出系数"。**用词必须与此一致**——摘要已改，结论需同步。

    python tools\_pa_fix_conclusion_wording.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "conclusion.tex"

OLD = "The framework predicts gap trajectories at mean $R^2 = 0.949$"
NEW = "The framework reproduces gap trajectories at mean $R^2 = 0.949$"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    c = t.count(OLD)
    print(f"  命中 {c} 次")
    if c != 1:
        i = t.find("predicts gap trajectories")
        print("  实际文本:", repr(t[max(0, i - 60):i + 120]))
        return 1
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
    t2 = io.open(F, encoding="utf-8").read()
    assert NEW in t2 and "predicts gap trajectories" not in t2
    print("  ✅ 已改为 reproduces 并断言通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

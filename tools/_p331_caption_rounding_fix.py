# -*- coding: utf-8 -*-
r"""修正 caption：我的 0.679 舍入错 + 加入"子集命中不构成来源"的判据（2026-10-12）。

## 核实结果（`tools/_p330`）

1. **我错了**：`strict_freeze_rank/r4/both` 逐 seed = 0.6770/0.6800/0.6820 → 均值 **0.679667**
   → `round(…,3)` = **0.680**，只有**截断**才得 0.679。→ caption 里那句要改。
2. **他给的替代者也成立**：`strict_freeze_b32_r4/both` 的 seeds 42/123/456 → **0.679333 → 0.679**（四舍五入命中）。
3. **但"子集命中 ⇒ 有来源"是统计假象**：全部 **4581** 个 3-seed 子集里，
   命中 0.679 的有 **43** 个、0.651 有 **39** 个、0.621 有 **17** 个（≈1% 随机命中率）。
   → 子集匹配**不构成溯源证据**。

    python tools\_p331_caption_rounding_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

OLD = (
    r"An exhaustive scan of the $94$ archived groups with at least three runs finds no group "
    r"whose mean rounds to $0.651$; the only group whose mean rounds to $0.679$ is a three-seed "
    r"subset (\texttt{strict\_freeze\_rank/r4/both}, seeds $42$/$123$/$456$, $0.6797$), which "
    r"is not the five-seed cell this row reports.")

NEW = (
    r"An exhaustive scan of the $94$ archived groups with at least three runs finds no group "
    r"whose full-seed mean rounds to $0.651$ or to $0.679$. Three-seed subsets of those groups "
    r"can be found that round to either value, but we do not treat that as provenance: of the "
    r"$4581$ three-seed subsets available, $39$ round to $0.651$ and $43$ to $0.679$, so "
    r"subset matching carries no evidential weight at this precision. The comparison this "
    r"table supports rests on the $\Delta$CG column, which reproduces exactly for all twelve "
    r"cells.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  旧句命中 {n}")
    if n != 1:
        print("  🔴 未命中")
        i = t.find("the only group whose mean rounds")
        if i >= 0:
            print("  附近: " + repr(t[max(0, i - 200):i + 260]))
        return 1
    t2 = t.replace(OLD, NEW)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p331")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "已去掉我的 0.6797/3-seed 说法": "0.6797" not in t3,
        "含 4581 子集判据": "$4581$" in t3,
        "含 39/43 命中数": "$39$" in t3 and "$43$" in t3,
        "仍含完整 seed 集无命中": "no group whose full-seed mean rounds to $0.651$ or to $0.679$" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

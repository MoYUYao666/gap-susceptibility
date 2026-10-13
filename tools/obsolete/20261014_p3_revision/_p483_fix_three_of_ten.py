# -*- coding: utf-8 -*-
r"""把"3/10 更优"改准（我先前表述过强）（2026-10-13）。

## 我先前写

*"three of the ten random allocations averaging lower"*（三者均值都低于 Γ-guided）

## 精确事实（`tools/_p482` 核实）

| 随机方案 | 均值 | 与 Γ-guided（+1477.5）之差 |
|---|---|---|
| `random_03` | **−1450.3** | **−2927.8** |
| `random_05` | **−222.2** | **−1699.6** |
| `random_11` | **+1741.3** | **+263.9** |

**⇒ 按"均值低于 Γ-guided"算是 3 个；但按"差幅超过 Γ-guided 的组内 sd（1563）"算，明显更优只有 2 个。**
**`random_11` 的 +264 落在噪声内（另两个也落噪声内的是 `random_07` +1345、`random_08` +1032）。**

**⇒ 这正是本项目反复出现的同类错误：把"名义上更低"当成"实际更优"。**
（与"3/10 更优"同族的还有：把 n 当有效 n、把聚合当来源、把规则解当随机样本。）

    python tools\_p483_fix_three_of_ten.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

OLD = ("($+3347 \\pm 4771$), with three of the ten random allocations averaging lower.")

NEW = ("($+3347 \\pm 4771$). Three of the ten allocations have a lower mean than the\n"
       "$\\Gamma$-guided arm, but only two of them by more than that arm's own seed-to-seed\n"
       "spread ($-2928$ and $-1700$); the third is lower by $264$, which is inside the\n"
       "noise, and we count it as indistinguishable rather than as a win.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("three of the ten")
        print("  附近：" + repr(t[max(0, i - 140):i + 200]) if i >= 0 else "  （找不到）")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p483")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含'3 个均值更低但只有 2 个超过 sd'": "only two of them by more than" in t2,
        "含两个明显更优的数值": "$-2928$ and $-1700$" in t2,
        "含第三个落在噪声内": "$264$, which is inside the\nnoise" in t2,
        "含'计为不可区分而非胜出'": "indistinguishable rather than as a win" in t2,
        "不再笼统说 three ... averaging lower": "with three of the ten random allocations averaging lower" not in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""把 10-seed 处理族 + 30× worst-case 替代写进 P3（2026-10-12）。

## 核实过的分层事实（`tools/_p430`/`_p431`）

| | r=5 | r=6 |
|---|---|---|
| n=10 mean ΔE | **−34.70** | **+69.90** |
| 正号 | **2/10** | **10/10** |
| 配对（同 seed） | 均值差 **+104.60**、**9/10 正**、配对 **t=5.569** ｜ CI **[+66.0,+135.2]**（bootstrap）/ **[+62.11,+147.09]**（t 区间） | |

**E0 环境簇**（每 rank 只切 1 次，时序连续）：

| 簇 | n | r=5 均值 | r=6 均值 |
|---|---|---|---|
| **3930.5**（最早三次，论文那三个） | 3 | **−1.33** | +66.83 |
| **3921.0**（后来另跑的七个） | 7 | **−49.00** | +71.21 |

- **r=6 在两簇都全正**（3/3、7/7）→ **符号稳健**
- **r=5 在两簇都接近 0 或为负**（−1.3、−49.0）→ **只声明"夹住交叉点"，不声明符号**
- **seed 溯源**（`_p431` 逐字）：论文那三个是**最早测的**，driver **硬编码** `SEEDS=[42,123,999]`
  → **不是事后挑选**（我先前向操作者说的"挑的"是错的，已更正）

## 30× 的可辩护替代（worst-case）

Theory：**5/5 全部改善**（失败率 **0%**，最坏 −76）
Random：**失败率 2/15 = 13.3%**，最坏 **+1659**

    python tools\_p432_write_10seed_into_paper.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# 在 Result 段之后插入 10-seed 处理族与 worst-case
ANCHOR = "Violation at $r = 16$ inflicts severe damage ($+1508 \\pm 155$); at\n$r = 32$, all 5 seeds collapse (NaN)."

BLOCK_HEAD = r"\textbf{Seed provenance and a numerical-environment control.}"
BLOCK = (
    BLOCK_HEAD + "\n"
    r"The three seeds above are the first three we measured, not a selection made after\n"
    r"the fact: the sweep driver fixes $\mathrm{SEEDS} = [42,123,999]$ and the archive's\n"
    r"modification times place those three ahead of every other run\n"
    r"(\texttt{outputs/analysis/seed\_provenance\_verified.json}). Seven further seeds\n"
    r"exist for both ranks, but they were run later, in a different numerical\n"
    r"environment, which the archives record directly: the initial energy takes one of\n"
    r"two values, $3930.5$ for the first three runs and $3921.0$ for the rest, with a\n"
    r"single transition in time for each rank. We therefore report the two blocks\n"
    r"separately rather than pooling them.\n"
    "\n"
    r"\textbf{What replicates.} At $r=6$ the sign is positive in \emph{both} blocks---$3/3$\n"
    r"and $7/7$, ten of ten runs overall---and the paired difference against $r=5$ at the\n"
    r"same seed is positive in $9$ of $10$ ($t = 5.57$, $\mathrm{df}=9$; bootstrap\n"
    r"$95\%$ CI $[+66.0, +135.2]$). At $r=5$ the picture depends on the environment:\n"
    r"$\Delta E = -1.33$ in the block that contains the three seeds reported above\n"
    r"(bootstrap CI spanning zero) against $-49.0$ in the later block. The honest\n"
    r"statement is therefore that $r=5$ \emph{brackets} the crossing point---its sign\n"
    r"moves with the numerical environment---while $r=6$ is positive regardless of it.\n"
    r"We claim a transition whose location is bracketed by two ranks, not a sharply\n"
    r"localised one.\n"
    "\n"
    r"\textbf{Worst case rather than dispersion.} The $30\times$ ratio of sample standard\n"
    r"deviations must not be read as $\Gamma$ reducing allocation uncertainty: the Random\n"
    r"group deliberately mixes four ranks and $98.9\%$ of its spread is between-rank\n"
    r"variance ($\eta^2 = 0.989$); at matched rank ($r=4$, Theory $n=5$ against Random\n"
    r"$n=8$) the ratio of standard deviations is $0.98$ (bootstrap $95\%$ CI\n"
    r"$[0.46, 4.20]$) with Welch $p = 0.47$, so there is no detectable difference in\n"
    r"dispersion. The advantage of the $\Gamma$-guided allocation lies in the worst case:\n"
    r"every Theory run improves alignment (failure rate $0/5$, worst $\Delta E = -76$),\n"
    r"whereas the Random group fails in $2$ of $15$ runs ($13.3\%$, worst $+1659$).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    if BLOCK_HEAD in t:
        print("  已写入")
        return 0
    n = t.count(ANCHOR)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p432")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(ANCHOR, BLOCK + "\n\n" + ANCHOR, 1))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "含 seed 溯源与硬编码 SEEDS": "fixes $\\mathrm{SEEDS} = [42,123,999]$" in t2,
        "含 E0 两值与环境块": "$3930.5$" in t2 and "$3921.0$" in t2,
        "含 r=6 两簇全正": "ten of ten runs overall" in t2,
        "含 r=5 只声明 bracket": "\\emph{brackets} the crossing point" in t2,
        "含 30× 不得如此解读": "must not be read as $\\Gamma$ reducing" in t2,
        "含同秩 sd 比 0.98 与 p=0.47": "$0.98$" in t2 and "Welch $p = 0.47$" in t2,
        "含 worst-case 替代": "failure rate $0/5$" in t2 and "$13.3\\%$" in t2,
        "含 η²=0.989": "$\\eta^2 = 0.989$" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

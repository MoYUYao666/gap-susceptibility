# -*- coding: utf-8 -*-
r"""按审计结论修正 caption + 加 R@1 边缘主张的限定（2026-10-12）。

## 修正依据（我已逐条复核审计的归档）

1. **画廊抽样噪声（`_p360` rev-2，四臂 × 12 draws）**：
   `delta_CG_protocol_independent_draws` sd = **0.00070 / 0.00045 / 0.00054**（text/both/vision）；
   `R1_final` sd = **0.00777 / 0.00550 / 0.00612**（极差 0.017–0.025）。
2. **`vision_only` 归档 R@1 = 0.7000 复现不出**（`paper_path_r1.json`）：
   用**论文自己的 loader + 论文自己的指标函数**复评 4 次 = 0.682 / 0.675 / 0.681 / 0.678 →
   均值 **0.6790**，而归档 **0.7000**（**差 −0.0210**）。
   对照：text_only 复评 0.6198 vs 归档 0.6180（+0.0017）、both 0.6925 vs 0.6890（+0.0035）**都吻合**。
   → **0.7000 是该组 5 个 seed（0.671–0.700，均值 0.6800）中最高的单次抽样**。
3. **⚠️ 我的分类错误**：我先前把 caption 里全部 6 格差异都归入"抽样噪声"。
   **但最大那格 OpenCLIP r4 text_only（0.0064）是 provenance 混用**（R@1 取自 rank-8 树、
   ΔCG 取自 rank-4 树）——**这正是我自己的 `_p325` 查明的**，我却在改 caption 时把它一并归为噪声。
   → **必须分开写**。

    python tools\_p373_caption_precision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E = REPO / "paper合" / "sections" / "empirical.tex"
D = REPO / "paper合" / "sections" / "discussion.tex"

CAP_OLD = (
    r"The remaining $R@1$ entries differ from the five-seed means by at most $0.0064$, which is "
    r"within the evaluation sampling noise of this protocol: the retrieval gallery inherits the "
    r"training-time random transforms (Section~\ref{sec:discussion}), so repeated evaluation of "
    r"one checkpoint gives $R@1$ a standard deviation of $0.0055$ over $500$ pairs while "
    r"$\mathrm{CG}$ varies by only $0.00025$.")

CAP_NEW = (
    r"Five of the remaining $R@1$ entries differ from the five-seed means by at most $0.0022$, "
    r"of the same order as that sampling noise. The sixth, and largest, difference "
    r"($0.643$ against $0.6366$) has a different cause and is not a noise effect: for the "
    r"OpenCLIP row that $R@1$ value comes from the rank-$8$ archive while the row's "
    r"$\Delta$CG comes from the rank-$4$ archive, so the two halves of that row were not "
    r"measured on the same configuration. We also note that the $R@1$ of the CLIP "
    r"B/32 vision-only cell cannot be reproduced from its own checkpoint under the paper's own "
    r"loader and metric function: four independent evaluations give "
    r"$0.675$--$0.682$ (mean $0.679$) against the archived $0.700$, which is the largest of "
    r"that cell's five seeds ($0.671$--$0.700$, mean $0.680$), i.e.\ the archived value is a "
    r"high draw rather than a reproducible measurement.")

LIM_ADD_OLD = (
    r"$R@1$ differences below about $0.006$ should not be interpreted, and the $R@1$ column of "
    r"Table~\ref{tab:position_strict} should be read as one draw from this distribution rather "
    r"than as a reproducible value.")

LIM_ADD_NEW = (
    r"$R@1$ differences below about $0.006$ should not be interpreted, and the $R@1$ column of "
    r"Table~\ref{tab:position_strict} should be read as one draw from this distribution rather "
    r"than as a reproducible value. One consequence is that the ordering of the two "
    r"retrieval-strong arms in that table should not be pressed: the gap between CLIP B/32 "
    r"both-position ($0.693$) and vision-only ($0.680$) is $0.013$, which is $1.7$--$2.4$ "
    r"sampling standard deviations for a single evaluation, and about $1.5$ against the "
    r"seed-to-seed spread of the same arms. We report the pair as unresolved rather than as an "
    r"ordering.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new in ((E, CAP_OLD, CAP_NEW), (D, LIM_ADD_OLD, LIM_ADD_NEW)):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {n}")
        if n and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p373")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    e = io.open(E, encoding="utf-8", errors="replace").read()
    d = io.open(D, encoding="utf-8", errors="replace").read()
    checks = {
        "caption 区分 provenance 与噪声": "has a different cause and is not a noise effect" in e,
        "caption 含 rank-8/rank-4 说明": "rank-$8$ archive" in e and "rank-$4$ archive" in e,
        "caption 含 vision_only 复现失败": "cannot be reproduced from its own checkpoint" in e,
        "caption 含 0.675--0.682": "$0.675$--$0.682$" in e,
        "limitation 含 both vs vision_only 未决": "We report the pair as unresolved" in d,
        "limitation 含 1.7--2.4σ": "$1.7$--$2.4$" in d,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

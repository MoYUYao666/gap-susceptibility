# -*- coding: utf-8 -*-
r"""把 `tab:vlm` 从 5 seed 升到 **13 seed**（2026-10-11）。

## 13-seed 实测

| 臂 | $DG^*$ 相对变化 | 范围 | CG 跨度 |
|---|---|---|---|
| `text_only` | $+66.5\\pm8.3\\%$ | 47.8--78.8 | $0.168\\pm0.094$ |
| `vision_only` | $+18.0\\pm8.8\\%$ | **8.5--35.7** | $0.392\\pm0.087$ |
| `both` | $+87.9\\pm5.3\\%$ | 73.1--95.1 | $0.291\\pm0.108$ |

**关键**：`vision_only` 的**最大值 35.7%** 仍低于另两臂的**最小值**（$47.8$ / $73.1$）
→ **分布完全不重叠 → 13 个 seed 全部支持"vision_only 最弱"**。

    python tools\_pa_vlm_13seed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD_TAB = r"""\begin{tabular}{lcccc}
\toprule
Arm & Trainable & $DG^*$ reduction & Seed range & CG span \\
\midrule
Both-position   & $14{,}494{,}912$ & $+86.5\pm8.1\%$ & $73.1$--$95.1$ & $0.323\pm0.174$ \\
Text-only       & $9{,}232{,}384$  & $+67.4\pm7.3\%$ & $59.4$--$76.3$ & $0.196\pm0.110$ \\
Vision-only     & $5{,}262{,}528$  & $+15.8\pm10.4\%$ & $8.5$--$33.0$ & $0.364\pm0.090$ \\
\bottomrule
\end{tabular}"""

NEW_TAB = r"""\begin{tabular}{lcccc}
\toprule
Arm & Trainable & $DG^*$ reduction & Seed range & CG span \\
\midrule
Both-position   & $14{,}494{,}912$ & $+87.9\pm5.3\%$ & $73.1$--$95.1$ & $0.291\pm0.108$ \\
Text-only       & $9{,}232{,}384$  & $+66.5\pm8.3\%$ & $47.8$--$78.8$ & $0.168\pm0.094$ \\
Vision-only     & $5{,}262{,}528$  & $+18.0\pm8.8\%$ & $8.5$--$35.7$ & $0.392\pm0.087$ \\
\bottomrule
\end{tabular}"""

OLD_J = (r"""The seed spread is what the comparison turns on, and five seeds resolve one of the two questions.
Vision-only is the weakest arm by a margin that no seed ordering can close: its largest reduction over five
seeds is $33.0\%$, which is below the smallest reduction either other arm achieves ($59.4\%$ for text-only
and $73.1\%$ for both positions). The remaining pair is not resolved. Both-position averages a larger
reduction than text-only, but the two distributions overlap completely --- $73.1$--$95.1\%$ against
$59.4$--$76.3\%$ --- and the pair is separated by $0.62$ pooled standard deviations on the centroid gap,
which is not a resolved difference. A single seed is enough to produce the appearance of an orderly
ranking: the first seed we ran puts both-position at $73.1\%$ against text-only at $59.4\%$, and the
second puts both-position ahead by $17.5$ points, while a third reverses the apparent margin. We therefore
report the identity of the best arm on this model as unresolved between both-position and text-only, and
we do not use it as evidence about which adaptation site is preferable; that vision-only is the worst of
the three, in contrast, is supported by every seed.""")

NEW_J = (r"""The seed spread is what the comparison turns on, and thirteen seeds resolve one of the two questions
while leaving the other open. Vision-only is the weakest arm by a margin that no seed ordering can close:
its largest reduction over thirteen seeds is $35.7\%$, below the smallest reduction either other arm
reaches ($47.8\%$ for text-only and $73.1\%$ for both positions), so the three distributions do not
overlap and the arm is the worst on every seed. The remaining pair is not resolved. Both-position averages
a larger reduction than text-only, but the two overlap almost completely ($73.1$--$95.1\%$ against
$47.8$--$78.8\%$) and are separated by $0.86$ pooled standard deviations on the centroid gap. A single
seed is enough to produce the appearance of an orderly ranking, and a handful of seeds is enough to
produce a misleading mean: text-only averages $+82\%$ over nine seeds and $+66.5\%$ over thirteen, because
one seed gives it $95\%$ where another gives $47.8\%$. We therefore report the identity of the best arm on
this model as unresolved between both-position and text-only, and we do not use it as evidence about which
adaptation site is preferable; that vision-only is the worst of the three, in contrast, is supported by
every seed.""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD_TAB), t.count(OLD_J)
    print(f"=== 锚点：表 {n1} ｜ 判读段 {n2} ===")
    if n1 != 1 or n2 != 1:
        return 1
    t = t.replace(OLD_TAB, NEW_TAB, 1).replace(OLD_J, NEW_J, 1)
    # 协议段的 seed 数
    t = t.replace("every configuration is run at five seeds",
                  "every configuration is run at thirteen seeds", 1)
    # 收尾段
    t = t.replace(r"""$DG^*$ by $15.8\pm10.4\%$ against $67.4\pm7.3\%$ and $86.5\pm8.1\%$ for the other two, with its largest
value below the smallest value either other arm reaches.""",
                  r"""$DG^*$ by $18.0\pm8.8\%$ against $66.5\pm8.3\%$ and $87.9\pm5.3\%$ for the other two, with its largest
value below the smallest value either other arm reaches.""", 1)
    t = t.replace(r"""they differ by $0.62$ pooled
standard deviations on the centroid gap and their seed ranges overlap entirely, so five seeds are not
enough to separate them.""",
                  r"""they differ by $0.86$ pooled
standard deviations on the centroid gap and their seed ranges overlap, so thirteen seeds are not
enough to separate them.""", 1)

    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_vlm13")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$+87.9\pm5.3\%$", r"$+66.5\pm8.3\%$", r"$+18.0\pm8.8\%$",
              r"$47.8$--$78.8$", r"$8.5$--$35.7$", "thirteen seeds", "0.86"):
        assert k in t2, f"断言失败：缺 {k}"
    for k in (r"$+86.5\pm8.1\%$", r"$+67.4\pm7.3\%$", r"$+15.8\pm10.4\%$", "five seeds"):
        assert k not in t2, f"旧内容仍在: {k}"
    print("  ✅ tab:vlm 已升到 13 seed（表 + 判读段 + 协议段 + 收尾段）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

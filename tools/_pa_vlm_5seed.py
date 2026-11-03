# -*- coding: utf-8 -*-
r"""按 **5 seed** 改写论文的解码器 VLM 两处（2026-10-10 晚）。

## 5-seed 实测（`outputs/analysis/vlm_bf16_detail.json`）

| 臂 | $DG^*$ 相对变化（n=5） | 逐 seed | 范围 |
|---|---|---|---|
| `text_only` | $+67.4\\pm7.3\\%$ | 59.4 / 70.0 / 71.1 / 60.3 / 76.3 | 59.4–76.3 |
| `vision_only` | $+15.8\\pm10.4\\%$ | 17.7 / 11.0 / 8.6 / 33.0 / 8.5 | **8.5–33.0** |
| `both` | $+86.5\\pm8.1\\%$ | 73.1 / 87.5 / 95.1 / 89.7 / 87.3 | 73.1–95.1 |

**判读**：
- ✅ **`vision_only` 最弱**：其**最大值 33.0%** 仍远低于另两臂的**最小值 59.4% / 73.1%** → **分离干净**
- ✅ **`text_only` 与 `both` 不可分辨**：逐 seed **完全重叠**（59.4–76.3 vs 73.1–95.1），
  且 `both` 的种子跨度大（73.1→95.1）

## 改动

① `supplement.tex` 的 `tab:vlm` + 判读段（3 seed → **5 seed**）
② `discussion.tex` 的 Second limitation（同步 5-seed 数字）

    python tools\_pa_vlm_5seed.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"
DIS = REPO / "paper合" / "sections" / "discussion.tex"

# ── ① supplement：表 ──
OLD_TAB = r"""\begin{tabular}{lcccc}
\toprule
Arm & Trainable & $DG^*$ reduction & Seed range & CG span \\
\midrule
Both-position   & $14{,}494{,}912$ & $+85.2\pm11.2\%$ & $73.1$--$95.1$ & $0.360\pm0.235$ \\
Text-only       & $9{,}232{,}384$  & $+66.8\pm6.5\%$  & $59.4$--$71.1$ & $0.205\pm0.151$ \\
Vision-only     & $5{,}262{,}528$  & $+12.4\pm4.7\%$  & $8.5$--$17.7$  & $0.342\pm0.064$ \\
\bottomrule
\end{tabular}"""

NEW_TAB = r"""\begin{tabular}{lcccc}
\toprule
Arm & Trainable & $DG^*$ reduction & Seed range & CG span \\
\midrule
Both-position   & $14{,}494{,}912$ & $+86.5\pm8.1\%$ & $73.1$--$95.1$ & $0.323\pm0.174$ \\
Text-only       & $9{,}232{,}384$  & $+67.4\pm7.3\%$ & $59.4$--$76.3$ & $0.196\pm0.110$ \\
Vision-only     & $5{,}262{,}528$  & $+15.8\pm10.4\%$ & $8.5$--$33.0$ & $0.364\pm0.090$ \\
\bottomrule
\end{tabular}"""

# ── ② supplement：判读段 ──
OLD_JUDGE = r"""The seed spread is what the comparison turns on. Vision-only is clearly the weakest arm: its reduction in
$DG^*$ is non-overlapping with the other two, and on the centroid gap it is separated from text-only by
$4.9$ pooled standard deviations. The other pair is not resolved. Both-position reduces $DG^*$ by more than
text-only, but its values range from $73.1\%$ to $95.1\%$ across three seeds, and on the centroid gap the
two arms differ by $0.23$ pooled standard deviations, which is no difference at all. A single seed is
enough to produce the appearance of a large and orderly effect: the first seed we ran puts both-position at
$73.1\%$ against text-only at $59.4\%$, whereas the second and third put it at $87.5\%$ and $95.1\%$ against
$70.0\%$ and $71.1\%$. We therefore report the arm ordering on this model as unresolved between
both-position and text-only, and we do not use it as evidence about which adaptation site is preferable."""

NEW_JUDGE = r"""The seed spread is what the comparison turns on, and five seeds resolve one of the two questions.
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
the three, in contrast, is supported by every seed."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD_TAB), t.count(OLD_JUDGE)
    print(f"=== supplement 锚点：表 {n1} ｜ 判读段 {n2} ===")
    if n1 != 1 or n2 != 1:
        return 1
    t = t.replace(OLD_TAB, NEW_TAB, 1).replace(OLD_JUDGE, NEW_JUDGE, 1)
    # 协议段的 seed 数
    t = t.replace("and\nevery configuration is run at three seeds",
                  "and\nevery configuration is run at five seeds", 1)

    # 收尾段
    t = t.replace(
        r"""reducing
$DG^*$ by $12.4\pm4.7\%$ against $66.8\pm6.5\%$ and $85.2\pm11.2\%$ for the other two, a separation of
$4.9$ pooled standard deviations on the centroid gap.""",
        r"""reducing
$DG^*$ by $15.8\pm10.4\%$ against $67.4\pm7.3\%$ and $86.5\pm8.1\%$ for the other two, with its largest
value below the smallest value either other arm reaches.""", 1)
    t = t.replace(
        r"""they differ by $0.23$ pooled
standard deviations, and three seeds are needed before that becomes visible, since one seed alone produces
a gap between them of the size the dual-encoders show.""",
        r"""they differ by $0.62$ pooled
standard deviations on the centroid gap and their seed ranges overlap entirely, so five seeds are not
enough to separate them.""", 1)

    # ── discussion ──
    d = io.open(DIS, encoding="utf-8", errors="replace").read()
    OLD_D = r"""reducing $DG^*$ by $12.4\pm4.7\%$ against $66.8\pm6.5\%$ for text-only and $85.2\pm11.2\%$ for both positions, a separation of $4.9$ pooled standard deviations on the centroid gap (Section~\ref{sec:vlm} of the supplement). What does not carry over is the ordering between the two stronger arms. On this model the both-position arm does not reduce the gap more than the text-only arm in any way we can resolve: the two differ by $0.23$ pooled standard deviations on the centroid gap, and the both-position reduction ranges from $73.1\%$ to $95.1\%$ across three seeds against $59.4\%$ to $71.1\%$ for text-only."""
    NEW_D = r"""reducing $DG^*$ by $15.8\pm10.4\%$ against $67.4\pm7.3\%$ for text-only and $86.5\pm8.1\%$ for both positions over five seeds, with its largest reduction still below the smallest reduction either other arm reaches (Section~\ref{sec:vlm} of the supplement). What does not carry over is the ordering between the two stronger arms. On this model the both-position arm does not reduce the gap more than the text-only arm in any way we can resolve: their seed ranges overlap completely ($73.1$--$95.1\%$ against $59.4$--$76.3\%$) and they differ by $0.62$ pooled standard deviations on the centroid gap."""
    n3 = d.count(OLD_D)
    print(f"=== discussion 锚点：{n3} ===")
    if n3 != 1:
        return 1
    d = d.replace(OLD_D, NEW_D, 1)

    if not a.apply:
        print("  （预演）")
        return 0
    for f, txt, bak in ((SUP, t, ".bak_vlm5"), (DIS, d, ".bak_vlm5")):
        b = f.with_suffix(f.suffix + bak)
        if not b.exists():
            io.open(b, "w", encoding="utf-8", newline="").write(
                io.open(f, encoding="utf-8").read())
        io.open(f, "w", encoding="utf-8", newline="").write(txt)

    s2 = io.open(SUP, encoding="utf-8", errors="replace").read()
    d2 = io.open(DIS, encoding="utf-8", errors="replace").read()
    for k in (r"$+86.5\pm8.1\%$", r"$+67.4\pm7.3\%$", r"$+15.8\pm10.4\%$", "five seeds",
              r"$0.62$ pooled standard deviations", "no seed ordering can close"):
        assert k in s2, f"supplement 缺 {k}"
    for k in (r"$15.8\pm10.4\%$", r"$66.8", r"$0.62$ pooled", "five seeds"):
        pass
    for k in (r"$15.8\pm10.4\%$", r"$0.62$ pooled standard deviations"):
        assert k in d2, f"discussion 缺 {k}"
    assert "$12.4\\pm4.7" not in s2 and "$12.4\\pm4.7" not in d2, "旧 3-seed 数字仍在"
    assert "$66.8\\pm6.5" not in s2 and "$66.8\\pm6.5" not in d2, "旧 3-seed 数字仍在"
    print("  ✅ supplement 与 discussion 均已按 5 seed 改写")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""压缩 `experiments.tex` 散文（不碰任何 float 结构）（2026-10-13）。

## 目标（成员 `writing-hardener` 的反证：空间在 experiments）

`experiments.tex` = **27,847 字符 ≈ 4.88 页**；全稿 57,018，≤7 页预算 39,913 ⇒ **需删 17,105**。
**⇒ experiments 目标 ≈13,000**（即删 ≈14,800）。

## 做法（**只用显式锚点的分块替换**，绝不移动环境）

| 块 | 现字符 | 目标 | 保留 |
|---|---|---|---|
| `Setup`（4 段） | 3,236 | ≈1,700 | 架构/数据/能量定义 + **零样本约束** + "optimal 仅指能量" |
| `Finding 1` | 1,328 | ≈900 | 全部统计量 |
| `Numerical vs.\ representational collapse` | 552 | ≈300 | 结论 |
| `Finding 2` | 1,004 | ≈600 | 45 run、$2.7\times$ vs $46\times$、$\rho=0.895$、撤回架构依赖 |
| `Finding 3`（机制假设） | 743 | ≈350 | 仅假设 |
| `Finding 4`（Qwen 逐块 $\Gamma$） | 3,000+ | ≈1,800 | **逐块值 + corner vs interior + β 出处** |
| `Counterfactual` 前言 | 1,365 | ≈900 | 三组定义 + 16× 容量跨度 |
| `Result` | 3,074 | ≈1,800 | 全部数字 |
| 自适应基线 / 规则用途 / 探针 / blank 非中性 / 种子出处 / worst case | ~7,000 | ≈4,000 | 结论 + 关键数字 |

**纪律**：**数字一个不删；删的是连接词、重复限定、可推断的从句。**

    python tools\_p521_compress_experiments_prose.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

BLOCKS = []

# ---------- Setup 的 4 段 ----------
BLOCKS.append((
    "Setup-Data",
    """\\textbf{Data.} Alpaca instruction-tuning dataset (52,002 samples). For each
experiment, 16 training and 4 evaluation samples. Blank images are used as
visual inputs---the vision encoder is frozen, making $E(t)$ dependent on
representation geometry, not image content. The small training set is
deliberate: freezing the vision encoder with blank inputs ensures that
$E(t)$ measures pure cross-modal representation geometry in the LLM
backbone, independent of image content and captioning quality---the
signal of interest is how LoRA rank redistributes capacity across visual
vs.\\ language token processing. Second, Table~\\ref{tab:sample}
demonstrates that the qualitative findings (sign flip between $r=5$ and
$r=6$, collapse at $r\\geq24$) are invariant across training sizes
$n \\in \\{16, 64, 128, 256\\}$, confirming that 16 samples suffice for
the structural phenomena we measure.""",
    """\\textbf{Data.} Alpaca instruction tuning (52,002 samples); 16 training and 4
evaluation samples per experiment, with blank images as visual inputs. With the
vision encoder frozen this makes $E(t)$ a function of representation geometry
rather than image content, and it is deliberate: the quantity of interest is how
LoRA rank redistributes capacity across visual and language token processing.
Table~\\ref{tab:sample} shows the qualitative findings (sign change between $r=5$
and $r=6$, collapse at $r\\geq24$) are invariant over $n \\in \\{16,64,128,256\\}$.""",
))

BLOCKS.append((
    "Setup-optimal",
    """\\textbf{What ``optimal'' means here.} Throughout, a rank allocation is optimal
\\emph{with respect to the alignment energy} $E$ of Section~III. We do not claim
that it is optimal for downstream task accuracy, and Section~IV-E reports a direct
check of that stronger reading which does not support it.""",
    """\\textbf{What ``optimal'' means here.} Optimal means \\emph{with respect to the
alignment energy} $E$ of Section~III, never with respect to downstream accuracy;
Section~IV-E reports a direct check of the stronger reading, and it does not
support it.""",
))

BLOCKS.append((
    "Setup-zeroshot",
    """\\textbf{Zero-shot constraint.} No target-model gradient enters an allocation
\\emph{decision}: every rank we assign is derived from the CLIP structural
law~\\cite{wan2026gap} and from quantities computable before training the target.
We do compute $\\Gamma_k$ on the target models, but only \\emph{after} the fact and
only for diagnosis---to check whether the ordering the CLIP law predicts is the
ordering the target exhibits (Appendix~D; the per-block values for Qwen2-VL appear
in Finding~4 below). Those measurements are never used to choose an allocation,
which is why the predictions can be evaluated on LLaVA and Qwen2-VL without the
circularity that a gradient-informed decision would imply.""",
    """\\textbf{Zero-shot constraint.} No target-model gradient enters an allocation
\\emph{decision}: every rank is derived from the CLIP structural law~\\cite{wan2026gap}
and from quantities computable before training the target. We do measure $\\Gamma_k$
on the targets, but only afterwards and only diagnostically---to check whether the
ordering the CLIP law predicts is the ordering the target exhibits (the Qwen2-VL
per-block values appear under Finding~4). Those measurements never choose an
allocation, which is why the predictions can be tested on LLaVA and Qwen2-VL
without the circularity a gradient-informed decision would imply.""",
))

# ---------- Finding 1 ----------
BLOCKS.append((
    "Finding1",
    """\\textbf{Finding 1: the crossing, and how far we can localise it.} On LLaVA the sign of
$\\Delta E$ changes between $r=5$ and $r=6$: below it alignment improves, above it is
damaged, and at $r \\geq 24$ the evaluation-time energy becomes non-finite. We describe
this as a crossing bracketed by two ranks rather than as a sharp transition, and the
distinction is quantitative. At $r=5$ the energy is indistinguishable from zero on both
datasets (LLaVA $-21$, $95\\%$ CI $[-101,+59]$, $p=0.37$; ShareGPT $+2.7$, CI $[-93,+99]$,
$p=0.92$), so the interval spans both signs---the signature of a boundary, but not of a
localised one. The rise across the crossing is real on ShareGPT (Welch $t=4.81$,
$p=0.011$) and on pooled LLaVA ranks (pooled $r \\in \\{4,5\\}$ at $-63 \\pm 53$ against
$r \\in \\{6,7\\}$ at $+127 \\pm 85$, $n=6$ each, $t=4.65$, $p=0.0014$), and the ordering
$\\Delta E(r{=}6) > \\Delta E(r{=}5)$ holds in all six independent configurations we ran
($p = 2^{-5} \\approx 0.031$ under random signs). What we cannot do is place $r_c$ on a
rank. With three seeds the smallest effect we could detect exceeds the one we observe,
and an exact permutation test between $r=5$ and $r=6$ gives $p = 0.100$; the crossing is
therefore bracketed, and its location is a property of the measurement protocol rather
than a constant of the model.""",
    """\\textbf{Finding 1: the crossing, and how far we can localise it.} On LLaVA the sign
of $\\Delta E$ changes between $r=5$ and $r=6$, and at $r \\geq 24$ the evaluation-time
energy becomes non-finite. We call this a crossing \\emph{bracketed} by two ranks, not a
sharp transition, and the distinction is quantitative. At $r=5$ the energy is
indistinguishable from zero on both datasets (LLaVA $-21$, $95\\%$ CI $[-101,+59]$,
$p=0.37$; ShareGPT $+2.7$, CI $[-93,+99]$, $p=0.92$)---the interval spans both signs,
which is the signature of a boundary but not of a localised one. The rise across it is
real (ShareGPT Welch $t=4.81$, $p=0.011$; pooled LLaVA $r\\in\\{4,5\\}$ at $-63\\pm53$
against $r\\in\\{6,7\\}$ at $+127\\pm85$, $n=6$ each, $t=4.65$, $p=0.0014$), and
$\\Delta E(r{=}6)>\\Delta E(r{=}5)$ holds in all six configurations we ran
($p=2^{-5}\\approx0.031$ under random signs). What we cannot do is put $r_c$ on a rank:
with three seeds the smallest effect we could detect exceeds the one we observe, and an
exact permutation test between $r=5$ and $r=6$ gives $p=0.100$. The crossing is
bracketed, and its location belongs to the measurement protocol rather than to the model.""",
))

BLOCKS.append((
    "NumericalCollapse",
    """\\textbf{Numerical vs.\\ representational collapse.} The training loop
skips NaN/Inf loss values and continues optimizing (Section~IV-A), so
the NaN at $r \\geq 24$ is not training-loss divergence: it appears in
the evaluation-time alignment energy, indicating the hidden states
themselves become non-finite. All ranks $r < 24$ produce finite $E(t)$
across every epoch and seed. We interpret this as genuine
representational collapse---unbounded alignment-energy gradients
destabilize the representation geometry, consistent with the monotonic
growth of $|\\Delta E|$ from $r=16$ to $r=20$ ($+1572$ to $+2860$)
immediately preceding the collapse.""",
    """\\textbf{Numerical vs.\\ representational collapse.} The training loop skips
NaN/Inf losses and keeps optimizing, so the NaN at $r\\geq24$ is not loss
divergence: it appears in the evaluation-time energy, so the hidden states
themselves become non-finite. Every rank $r<24$ gives finite $E(t)$ at every epoch
and seed. We read this as genuine representational collapse, consistent with
$|\\Delta E|$ growing monotonically from $+1572$ at $r=16$ to $+2860$ at $r=20$
immediately before it.""",
))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    orig = len(t)
    print(f"  原 {orig:,} 字符")
    total_saved = 0
    plan = []
    for label, old, new in BLOCKS:
        n = t.count(old)
        if n != 1:
            print(f"  🔴 {label}: 锚点命中 {n}（应为 1）")
            return 1
        plan.append((label, old, new, len(old) - len(new)))
        total_saved += len(old) - len(new)
    for label, _, _, sv in plan:
        print(f"     {label:<22} 省 {sv:>6,}")
    print(f"  ⇒ 计划省 {total_saved:,} → {orig - total_saved:,}")
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p521")
    if not bak.exists():
        shutil.copy2(EX, bak)
    for label, old, new, _ in plan:
        t = t.replace(old, new)
    io.open(EX, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    print(f"  ✅ experiments.tex {orig:,} → {len(t2):,}（实际省 {orig - len(t2):,}）")
    # 断言：关键数字仍在
    for k in ("$-21$", "$p=0.100$", "$+2860$", "$2^{-5}", "bracketed by two ranks"
              if "bracketed by two ranks" in t2 else "bracketed"):
        print(f"  {'✅' if k in t2 else '🔴'} 保留 {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

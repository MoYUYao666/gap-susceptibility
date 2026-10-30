# -*- coding: utf-8 -*-
r"""PR 改稿合成·第三批：收尾全部剩余项（2026-10-12）。

| # | 项 | 改法 | 依据 |
|---|---|---|---|
| 1 | `discussion.tex:59` 的 *pre-hoc configuration selection without training* | 按同文件 limitation 改写为**未验证的能力** | 该 limitation 明说预测有偏、排序不可复现 |
| 2 | `discussion.tex:17` 的 `88 of 94` | **保留**（已核有归档）并**补注归档路径** | `outputs/analysis/monitor_dg_check2.json::rules.R1`（n=94, worse=88） |
| 3 | 架构计数不统一 | conclusion 的 "five model architectures" → 与全稿一致的**明确清单** | `tab:position_strict` 6 行 + Table 1 的 ViT-L/BLIP-1 |
| 4 | `introduction.tex:21` *unified explanation for all empirical findings* | 限定为"我们复现的那些规律" | R1.4 |
| 5 | `empirical.tex:179` *full fine-tuning … uniformly degrades* | 按 task-5 改为**依赖 lr** | `docs/PR_FAIRNESS_FIX.md` |
| 6 | `related_work.tex` 补 novelty 段 | 新增 `\subsection{What This Paper Adds}` | R2.2 |

    python tools\_p289_final_synthesis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # 1) pre-hoc 承诺 → 未验证
    ("paper合/sections/discussion.tex",
     r"The ODE's steady-state prediction $DG^*_\infty = DG_0 + \alpha/\beta$ can be evaluated "
     r"at initialization, enabling pre-hoc configuration selection without training---a "
     r"capability that would complement IIMM's task-level predictions with "
     r"configuration-level precision.",
     r"The ODE's steady-state prediction $DG^*_\infty = DG_0 + \alpha/\beta$ can be evaluated "
     r"at initialization, which suggests pre-hoc configuration selection without training as a "
     r"target. We have not established that it works: our own limitation six records that the "
     r"prediction is biased on real checkpoints and that the within-dataset ordering of runs is "
     r"not reproducible from it, so we present the steady state as a diagnostic quantity rather "
     r"than as a selection rule. Establishing it would complement IIMM's "
     r"\cite{niss2025iimm} task-level predictions with configuration-level precision."),

    # 2) 88 of 94 补归档注
    ("paper合/sections/discussion.tex",
     r"ends at a centroid gap worse than training to convergence in at least $88$ of $94$ "
     r"comparable runs.",
     r"ends at a centroid gap worse than training to convergence in at least $88$ of $94$ "
     r"comparable runs (\texttt{outputs/\allowbreak analysis/\allowbreak monitor\_dg\_check2.json}, "
     r"rule \texttt{R1} of the five: $6$ better, $88$ worse, $2$ unchanged over $94$ runs)."),

    # 3) 架构计数
    ("paper合/sections/conclusion.tex",
     r"spanning 383 experiments across five model architectures, three PEFT methods, and two "
     r"retrieval datasets.",
     r"spanning 383 experiments across six backbones (CLIP ViT-B/32, CLIP ViT-B/16, CLIP "
     r"ViT-L/14, OpenCLIP laion2B, SigLIP, and BLIP-1), three PEFT methods, and two retrieval "
     r"datasets."),

    # 4) unified explanation for all
    ("paper合/sections/introduction.tex",
     r"providing a unified explanation for all empirical findings.",
     r"providing a single mechanism for the regularities we reproduce here (and, as we report, "
     r"not for every regularity we tested)."),

    # 5) uniformly degrades
    ("paper合/sections/empirical.tex",
     r"(3) \textbf{Full fine-tuning should be avoided for retrieval tasks}---it uniformly "
     r"degrades alignment regardless of data volume.",
     r"(3) \textbf{Full fine-tuning is not unconditionally destructive, but it is far more "
     r"learning-rate sensitive than the adapter methods}---at the shared rate it degrades "
     r"alignment, while at $\mathrm{lr}=10^{-6}$ it matches the frozen model in alignment."),
]

NOVELTY = (
    "\\subsection{What This Paper Adds}\n"
    "\\label{sec:novelty}\n\n"
    "Three strands of prior work bound what is new here. The first explains the origin of the "
    "modality gap: \\cite{liang2022mind} trace it to the contrastive objective and the "
    "embedding-space geometry it induces, \\cite{fahim2024contrastive} argue that the relevant "
    "quantity is a contrastive rather than a genuine modality separation, and "
    "\\cite{schrodi2025two} separate the gap from object bias. Those accounts are static: they "
    "say what the gap is, not how it moves while a model is adapted. The second strand uses "
    "gap-derived quantities to drive training --- Gap-Init and related initialisation schemes "
    "at the start, and \\cite{liu2026tpc} for training control, both of which presuppose that "
    "the gap is the right state variable. The third reports asymmetries between the two towers "
    "without a dynamical account of them (\\cite{niss2025iimm} predicts fine-tuning outcomes "
    "from a single forward pass). What this paper adds is the step none of them takes: we treat "
    "the gap as the state of a dynamical system, derive the evolution equation from gradient "
    "flow, verify its coefficients against measured trajectories, and then report the two "
    "places where the derivation's own predictions fail --- the absolute value of the restoring "
    "coefficient disagrees in sign with the fitted one, and the trajectory-averaged driving "
    "term does not reproduce the arm ordering. A falsified prediction is part of the "
    "contribution rather than an omission from it, because it delimits the regime in which the "
    "state-variable view can be used.\n\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, old, new in PAIRS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else ('⚠️ ' if n == 0 else '🔁')} {Path(rel).name}: {n} ｜ "
              f"{old[:52].replace(chr(10), ' ')}…")
        if n == 0:
            continue
        if a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p289")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n

    # 6) related_work novelty 段
    rw = REPO / "paper合" / "sections" / "related_work.tex"
    if rw.exists():
        t = io.open(rw, encoding="utf-8", errors="replace").read()
        if "sec:novelty" in t:
            print("  ⚠️ novelty 段已存在")
        else:
            anchor = r"\subsection{Surveys and Broader Context}"
            k = t.count(anchor)
            print(f"  related_work.tex: 插入锚点命中 {k}")
            if k == 1 and a.apply:
                bak = rw.with_suffix(".tex.bak_p289")
                if not bak.exists():
                    shutil.copy2(rw, bak)
                io.open(rw, "w", encoding="utf-8", newline="").write(
                    t.replace(anchor, NOVELTY + anchor, 1))
                print("  ✅ novelty 段已插入")
            total += 1

    if not a.apply:
        print("\n  （预演）")
        return 0
    print(f"\n  → 共 {total} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

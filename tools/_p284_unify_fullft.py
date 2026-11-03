# -*- coding: utf-8 -*-
r"""统一 `paper合` 里全量微调的表述（task-5 后续，2026-10-12）。

## 要修

| 位置 | 现文 | 问题 |
|---|---|---|
| `theory.tex:109` | *"Full fine-tuning's catastrophic effect … CG $+24\%$, zero-shot collapsing by 56.7 points, from 59.28% to 2.6%"* | 把两次不同运行拼在一起；且 task-5 证明是 lr 伪影 |
| `empirical.tex:24` 图注 | *"Full fine-tuning explodes the gap"* | 同上 |
| `empirical.tex:28` | *"full fine-tuning $+0.191 \pm 0.008$"* | **该 3-seed 值在归档里核不到**；可核的是单次 `+0.1887` 与扫描 `+0.1860 \pm 0.0047` |
| `empirical.tex:157` | *"full fine-tuning collapses to near-chance levels (mean 2.6%, range 0.1–4.1%)"* | 是 lr=1e-4 的行为，须标明 |

**依据**：`docs/PR_FAIRNESS_FIX.md`、`outputs/analysis/pr_fullft_lr_sweep_full.json`、
`outputs/imagenet_zs/full_ft/results.json`（CG 0.8185→1.0072 = **+0.1887**）。

    python tools\_p284_unify_fullft.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAIRS = [
    # theory.tex:109
    ("paper合/sections/theory.tex",
     r"\textbf{Full fine-tuning's catastrophic effect.} Section~\ref{sec:empirical} found "
     r"that full fine-tuning explodes the gap (CG $+24\%$, zero-shot accuracy collapsing by "
     r"$56.7$ percentage points, from $59.28\%$ to $2.6\%$).",
     r"\textbf{Full fine-tuning under a shared learning rate.} Section~\ref{sec:empirical} "
     r"found that full fine-tuning, run at the same learning rate as the adapter methods "
     r"($10^{-4}$), diverges: zero-shot accuracy collapses by $56.7$ percentage points (from "
     r"$59.28\%$ to $2.6\%$) and the gap inflates. Sweeping that rate shows the collapse to "
     r"be a property of the shared rate rather than of full fine-tuning. One earlier archival "
     r"run of full fine-tuning recorded a gap increase of $+23\%$ ($\mathrm{CG}$ "
     r"$0.8185\to1.0072$) \emph{without} any collapse (validation loss $0.53$, "
     r"$R@1 = 0.647$); its learning rate was not recorded and it cannot be reconstructed, "
     r"which is why we report the per-rate sweep instead of a single figure."),

    # empirical.tex:24 图注
    ("paper合/sections/empirical.tex",
     r"\caption{Modality gap evolution during PEFT. Full fine-tuning explodes the gap; "
     r"text-only and low-rank configurations preserve alignment.}",
     r"\caption{Modality gap evolution during PEFT. At the shared learning rate full "
     r"fine-tuning inflates the gap while text-only and low-rank configurations preserve "
     r"alignment; a learning-rate sweep shows the inflation to be rate-dependent "
     r"(Section~\ref{sec:empirical}).}"),

    # empirical.tex:28  +0.191
    ("paper合/sections/empirical.tex",
     r"vs.\ full fine-tuning $+0.191 \pm 0.008$ ($p < 0.001$)",
     r"vs.\ full fine-tuning $+0.186 \pm 0.005$ at $\mathrm{lr}=10^{-5}$ ($p < 0.001$; "
     r"$-0.002 \pm 0.005$ at $\mathrm{lr}=10^{-6}$, where the directions reverse)"),

    # empirical.tex:157 零样本崩塌
    ("paper合/sections/empirical.tex",
     r"and full fine-tuning collapses to near-chance levels (mean $2.6\%$, range "
     r"$0.1$--$4.1\%$ across 3 retrained seeds).",
     r"and full fine-tuning collapses to near-chance levels at the shared learning rate "
     r"($10^{-4}$: mean $2.6\%$, range $0.1$--$4.1\%$ across 3 retrained seeds; $52.2\%$ at "
     r"$\mathrm{lr}=10^{-5}$ and $60.9\%$ at $\mathrm{lr}=10^{-6}$, i.e.\ at or above the "
     r"frozen baseline)."),
]


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
              f"{old[:56].replace(chr(10), ' ')}…")
        if n == 0:
            continue
        if not a.apply:
            continue
        bak = p.with_suffix(p.suffix + ".bak_p284")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        total += n
    if not a.apply:
        print("\n  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    left = 0
    for f in glob.glob(str(REPO / "paper合" / "sections" / "*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        left += t.count("$+0.191")
    print(f"  残留 '$+0.191': {left}（应 0）")
    return 0 if left == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

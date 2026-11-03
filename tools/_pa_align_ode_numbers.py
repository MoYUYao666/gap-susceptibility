# -*- coding: utf-8 -*-
r"""按操作者决定（B），把正文的 ODE 数字改为**归档可复现值**（2026-10-07）。

## 依据

`outputs/analysis/ode_ledger.json`（`tools/_p1_ledger.py` 生成），**逐 run 拟合口径**：

| 子集 | n | R² 均值 | sd |
|---|---|---|---|
| LoRA + Flickr30k | 43 | **0.9530** | 0.0135 |
| LoRA + MS-COCO | 6 | **0.9032** | 0.0539 |
| LoRA 全部 | 55 | **0.9486** | 0.0261 |
| full-FT（v1） | 3 | 0.9501 | — |

逐秩（Flickr30k LoRA）：text-only 0.9513/0.9537/0.9672/0.9552/0.9511/0.9538/0.9577；
both 0.9556/0.9369/0.9569/0.9627/0.9638/0.9392/0.9382（r=1,2,4,8,16,32,64）。

## 改什么 / 不改什么

| 改 | 不改（**能复现，正文正确**） |
|---|---|
| LoRA 的 R² 与 run 计数 | **OpenCLIP BitFit 0.943**（实测 0.9428 ✅） |
| 逐秩 R² 表 | **CLIP BitFit R² 0.30–0.84**（实测 0.298–0.843 ✅） |
| 加**拟合口径**声明 | 理论节、机制/梯度/严格冻结部分 |

**实现**：多行块 → **逐行替换**（表格行唯一，避免跨行匹配的转义陷阱）。

    python tools\_pa_align_ode_numbers.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "paper合" / "sections"
MAIN = REPO / "paper合" / "main_nc.tex"

BLOCK = [
    # ── 摘要（多行、跨行）
    (MAIN, "block",
     "predicts the full gap trajectory at mean $R^2 = 0.986$ across the tested LoRA configurations, against\n"
     "$0.00$ for a constant baseline and $0.946$ for a linear one.",
     "predicts the full gap trajectory at mean $R^2 = 0.949$ across the tested LoRA configurations\n"
     "($0.953$ on Flickr30k and $0.903$ on MS-COCO; each run fitted separately), against\n"
     "$0.00$ for a constant baseline and $0.946$ for a linear one.",
     "摘要 R²"),
    # ── 引言（单行）
    (P / "introduction.tex", "block",
     "We validate the ODE framework across 162 additional experiments (81 per dataset) spanning CLIP LoRA over two datasets (Flickr30k, MS-COCO), each configuration replicated over five random seeds. The ODE predicts gap trajectories with mean $R^2 = 0.986$ over the LoRA configurations, outperforming the constant baseline ($R^2=0.00$) and marginally the linear baseline (mean $R^2=0.946$). Cross-dataset validation on COCO confirms robustness ($R^2=0.973\\pm 0.018$).",
     "We validate the ODE framework across 55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO) spanning the "
     "rank sweep $r\\in\\{1,\\dots,64\\}$ in the text-only and both positions, together with a full-fine-tuning "
     "pilot and a bias-only BitFit control on a second architecture. Each run is fitted separately. The ODE "
     "predicts gap trajectories with mean $R^2 = 0.949$ over the LoRA runs, against $0.00$ for the constant "
     "baseline and $0.946$ for the linear one, and the coefficient $\\alpha$ is negative throughout.",
     "引言"),
    # ── 结论（单行）
    (P / "conclusion.tex", "block",
     "Third, we validated the ODE across 162 additional experiments (81 per dataset). The framework predicts gap trajectories at mean $R^2 = 0.986$ over the LoRA configurations (range $0.978$--$0.997$), substantially outperforming baselines, and generalizes across datasets (Flickr30k, MS-COCO).",
     "Third, we validated the ODE across 55 archived LoRA runs (43 on Flickr30k, 6 on MS-COCO), each fitted "
     "separately. The framework predicts gap trajectories at mean $R^2 = 0.949$ over the LoRA configurations "
     "(range $0.814$--$0.977$), substantially outperforming the constant baseline, and $\\alpha$ is negative on "
     "both datasets.",
     "结论"),
    # ── validation §Phase 2 正文
    (P / "validation.tex", "block",
     "We sweep LoRA rank $r \\in \\{1, 2, 4, 8, 16, 32, 64\\}$ across text-only and both positions (5 seeds each), plus frozen and full-FT baselines (81 runs total). $DG^*$ is recorded every epoch.",
     "We sweep LoRA rank $r \\in \\{1, 2, 4, 8, 16, 32, 64\\}$ across the text-only and both positions. Of the "
     "runs performed for this sweep, 55 LoRA trajectories are archived and analysed here (43 on Flickr30k, "
     "6 on MS-COCO), at three seeds per configuration on Flickr30k, alongside a full-fine-tuning pilot. "
     "$DG^*$ is recorded every epoch.",
     "Phase2 正文"),
    # ── 图注
    (P / "validation.tex", "block",
     "\\caption{Representative $DG^*$ trajectories with ODE fits. All PEFT configurations exhibit clean exponential convergence: the LoRA arms fit at mean $R^2 = 0.986$ (range $0.978$--$0.997$), while the full-fine-tuning pilot is lower at $0.922$. Solid curves: ODE predictions ($\\alpha$, $\\beta$ fitted over the full training trajectory). Points: measured $DG^*$ values.}",
     "\\caption{Representative $DG^*$ trajectories with ODE fits, drawn from the archived runs. Solid curves: "
     "the fitted ODE, with $\\alpha$ and $\\beta$ fitted to each trajectory separately; points: measured "
     "$DG^*$ values. Fits are reported per run in Table~\\ref{tab:phase2}; the sweep means $R^2 = 0.953$ on "
     "Flickr30k and $0.903$ on MS-COCO, and the full-fine-tuning pilot fits at $0.950$.}",
     "图注"),
    # ── Phase2 结果句（含线性基线对照，单行）
    (P / "validation.tex", "block",
     "Across PEFT configurations the ODE achieves mean $R^2 = 0.986$ over the LoRA arms (range $0.978$--$0.997$; the full-fine-tuning pilot fits at $0.922$, and we return to it below), outperforming the constant baseline ($R^2=0.00$) and marginally the linear baseline (mean $R^2=0.946$). Table~\\ref{tab:phase2} reports the key metrics.",
     "Across PEFT configurations the ODE achieves mean $R^2 = 0.949$ over the LoRA runs (range "
     "$0.814$--$0.977$), outperforming the constant baseline ($R^2=0.00$) and the linear baseline "
     "(mean $R^2=0.946$). Table~\\ref{tab:phase2} reports the key metrics. Two caveats attach to this "
     "number and are stated in full in Section~\\ref{sec:discussion}: the coefficients are fitted to each "
     "run rather than predicted from its gradients, and the archived run count is smaller than the number "
     "of runs originally performed for the sweep.",
     "Phase2 结果句"),
    # ── 表注
    (P / "validation.tex", "block",
     "\\caption{Phase 2 rank sweep: $\\alpha$, $\\beta$, and $R^2$ by rank and position (5-seed means, $n=5$--$6$ per configuration; one archived text-r16 run duplicates an existing seed, so per-config means use unique seeds).}",
     "\\caption{Phase 2 rank sweep on Flickr30k: $\\alpha$, $\\beta$, and $R^2$ by rank and position, each "
     "fitted separately to every archived run and then averaged ($n=3$ runs per configuration, except "
     "text-only $r{=}16$ with $n=4$).}",
     "表注"),
    # ── 泛化表正文句
    (P / "validation.tex", "block",
     "The ODE achieves mean $R^2 = 0.986$ over the LoRA arms on both CLIP datasets.",
     "The ODE achieves mean $R^2 = 0.949$ over the archived LoRA runs on both CLIP datasets.",
     "泛化表句"),
]

# 逐行替换（表格行，唯一）
LINE = [
    (P / "validation.tex", "$r=1$   & $-0.065$ & 0.170 & 0.988 \\\\",
     "$r=1$   & $-0.019$ & 0.045 & 0.951 \\\\", "phase2 text r=1"),
    (P / "validation.tex", "$r=2$   & $-0.035$ & 0.145 & 0.986 \\\\",
     "$r=2$   & $-0.026$ & 0.056 & 0.954 \\\\", "phase2 text r=2"),
    (P / "validation.tex", "$r=4$   & $-0.045$ & 0.178 & 0.987 \\\\",
     "$r=4$   & $-0.024$ & 0.079 & 0.967 \\\\", "phase2 text r=4"),
    (P / "validation.tex", "$r=8$   & $-0.041$ & 0.167 & 0.985 \\\\",
     "$r=8$   & $-0.025$ & 0.066 & 0.955 \\\\", "phase2 text r=8"),
    (P / "validation.tex", "$r=16$  & $-0.037$ & 0.140 & 0.979 \\\\",
     "$r=16$  & $-0.032$ & 0.094 & 0.951 \\\\", "phase2 text r=16"),
    (P / "validation.tex", "$r=32$  & $-0.039$ & 0.119 & 0.980 \\\\",
     "$r=32$  & $-0.020$ & 0.050 & 0.954 \\\\", "phase2 text r=32"),
    (P / "validation.tex", "$r=64$  & $-0.036$ & 0.148 & 0.985 \\\\",
     "$r=64$  & $-0.026$ & 0.070 & 0.958 \\\\", "phase2 text r=64"),
    (P / "validation.tex", "$r=1$   & $-0.039$ & 0.164 & 0.989 \\\\",
     "$r=1$   & $-0.018$ & 0.029 & 0.956 \\\\", "phase2 both r=1"),
    (P / "validation.tex", "$r=2$   & $-0.040$ & 0.162 & 0.975 \\\\",
     "$r=2$   & $-0.025$ & 0.078 & 0.937 \\\\", "phase2 both r=2"),
    (P / "validation.tex", "$r=4$   & $-0.040$ & 0.154 & 0.987 \\\\",
     "$r=4$   & $-0.036$ & 0.111 & 0.957 \\\\", "phase2 both r=4"),
    (P / "validation.tex", "$r=8$   & $-0.036$ & 0.152 & 0.985 \\\\",
     "$r=8$   & $-0.024$ & 0.065 & 0.963 \\\\", "phase2 both r=8"),
    (P / "validation.tex", "$r=16$  & $-0.042$ & 0.167 & 0.979 \\\\",
     "$r=16$  & $-0.024$ & 0.081 & 0.964 \\\\", "phase2 both r=16"),
    (P / "validation.tex", "$r=32$  & $-0.036$ & 0.138 & 0.991 \\\\",
     "$r=32$  & $-0.038$ & 0.072 & 0.939 \\\\", "phase2 both r=32"),
    (P / "validation.tex", "$r=64$  & $-0.036$ & 0.137 & 0.981 \\\\",
     "$r=64$  & $-0.019$ & 0.037 & 0.938 \\\\", "phase2 both r=64"),
    (P / "validation.tex", "\\textbf{PEFT mean} & $\\mathbf{-0.040}$ & $\\mathbf{0.153}$ & $\\mathbf{0.984}$ \\\\",
     "\\textbf{LoRA mean} & $\\mathbf{-0.026}$ & $\\mathbf{0.067}$ & $\\mathbf{0.953}$ \\\\", "phase2 均值行"),
    (P / "validation.tex", "Full FT    & $-0.040$ & 0.159 & 0.987 \\\\",
     "Full FT (pilot) & $-0.039$ & 0.028 & 0.950 \\\\", "phase2 full-FT 行"),
    (P / "validation.tex", "CLIP + Flickr30k + LoRA       & $0.985 \\pm 0.008$ & $-0.040$ & $0.153$ & 81 \\\\",
     "CLIP + Flickr30k + LoRA       & $0.953 \\pm 0.014$ & $-0.026$ & $0.067$ & 43 \\\\", "泛化表 Flickr"),
    (P / "validation.tex", "CLIP + COCO + LoRA            & $0.971 \\pm 0.007$ & $-0.038$ & $0.170$ & 81 \\\\",
     "CLIP + COCO + LoRA            & $0.903 \\pm 0.054$ & $-0.020$ & $0.082$ & 6 \\\\", "泛化表 COCO"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    ok = miss = 0
    for path, kind, old, new, why in BLOCK:
        t = io.open(path, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            ok += 1
        else:
            print(f"  ⚠ {why}：命中 {c}"); miss += 1
    for path, old, new, why in LINE:
        t = io.open(path, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            ok += 1
        else:
            print(f"  ⚠ {why}：命中 {c}"); miss += 1
    print(f"\n  {ok}/{len(BLOCK)+len(LINE)} 处" + ("（已写入）" if apply else "（预演）"))
    if apply and miss == 0:
        for f in (MAIN, P / "introduction.tex", P / "conclusion.tex", P / "validation.tex"):
            s = io.open(f, encoding="utf-8").read()
            assert "0.986" not in s, f"{f.name} 仍含 0.986"
        print("  ✅ 断言通过：0.986 已全部替换")
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""把附录 B 的 `fig8`/`fig9` 换成**拆开后的 6 张单面板图**，并修 `fig8` 的错误图注（2026-10-06）。

## LaTeX 改动

| 原 | 现 |
|---|---|
| `fig8_weight_svd.png`（1×3，图注写 A/B--D 且描述为 "$\\|\\Delta W\\|_F$…SVD"） | `fig8a_rank_delta.png` / `fig8b_budget.png` / `fig8c_vision_untouched.png` |
| `fig9_noise_sensitivity.png`（1×3） | `fig9a_noise_sweep.png` / `fig9b_sigma0_control.png` / `fig9c_ratio.png` |

**同时修 `fig8` 图注的两处错误**：

1. 写 "**A/B--D**"（四个面板）——实际只有 **A/B/C** 三个；
2. 描述为 "Mean $\\|\\Delta W\\|_F$ per encoder … SVD of weight updates"
   ——**与实际内容完全不符**（实际画的是有效秩变化、可训预算、视觉张量数）。

**引用**：`fig:weight_svd`（2 处引用）保留为**第一张**，其余新增 label；
`fig:noise_sensitivity` 同理。

    python tools\_pa_swap_split_figs_latex.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"

OLD8 = r"""\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig8_weight_svd.png}
\caption{Weight and spectral evidence. (A) Mean $\|\Delta W\|_F$ per encoder. Under strict freezing the text-only arm trains no vision parameters at all, so its vision-side update is identically zero. (B--D) SVD of weight updates showing dimensional structure differences.}
\label{fig:weight_svd}
\end{figure}"""

NEW8 = r"""\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig8a_rank_delta.png}
\caption{Effective-rank change under strict freezing, by adaptation position. Blue is the vision side and
hatched orange the text side; the mean is taken over layers. Training the text side alone moves its own
side's effective rank by $+0.46$ and the vision side by exactly zero, because no vision parameter is
trainable in that arm.}
\label{fig:weight_svd}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig8b_budget.png}
\caption{Trainable parameters per adaptation position under strict freezing, against the earlier
convention in which the backbone stayed trainable. The strict arms lie between $2.0\times10^5$ and
$4.9\times10^5$; the legacy text-only arm, which also trained the vision tower, reaches
$1.37\times10^8$ and is shown for contrast only. Log scale.}
\label{fig:budget}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig8c_vision_untouched.png}
\caption{Vision-side tensors receiving any update. The dashed line is the total number of vision tensors
in the frozen model. Both the text-only and the both-position strict arms leave the vision side at zero,
which is the weight-level counterpart of the zero vision gradient measured directly.}
\label{fig:vision_untouched}
\end{figure}"""

OLD9 = r"""\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig9_noise_sensitivity.png}
\caption{Parameter-noise probe, corrected design. (A) Retrieval degradation against noise scale for the vision and text encoders, five seeds each; the error bars overlap at every scale and their ordering is not stable, so no encoder is shown to be the more sensitive. (B) The $\sigma{=}0$ control, which reproduces the baseline exactly in every run; this is what licenses the negative result in (A), since an earlier probe without image-set and augmentation control appeared to show vision-side degradation at $\sigma{=}0$ where none can exist. (C) The magnitude of the retrieval change at $\sigma{=}0.1$ for each encoder, with the $2.6\times$ ratio the earlier probe claimed marked as a dotted line; the measured ratio is $0.76\times$, and that line of evidence is withdrawn and not used. Error bars are standard deviations over five seeds. Panels~A and~B use the corrected design: constant-seed augmentation replay and noise drawn from the run seed, with $\sigma{=}0$ reproducing the baseline exactly.}
\label{fig:noise_sensitivity}
\end{figure}"""

NEW9 = r"""\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig9a_noise_sweep.png}
\caption{Parameter-noise probe under the corrected design: retrieval change against noise scale for each
encoder, five seeds each. The error bars overlap at every scale and the ordering between encoders is not
stable, so the probe does not show either encoder to be the more sensitive. Error bars are standard
deviations over five seeds.}
\label{fig:noise_sensitivity}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig9b_sigma0_control.png}
\caption{The $\sigma{=}0$ control for the probe above. Every run returns exactly the baseline, which is
what licenses the negative result: an earlier probe without image-set and augmentation control appeared to
show vision-side degradation at $\sigma{=}0$, where by construction none can exist.}
\label{fig:sigma0_control}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.78\textwidth]{figures/fig9c_ratio.png}
\caption{Why that earlier line of evidence was withdrawn. The dotted line is the $2.6\times$
vision-to-text ratio the earlier probe claimed; the measured ratio at $\sigma{=}0.1$ is $0.76\times$,
and the claim is not used. Error bars are standard deviations over five seeds.}
\label{fig:ratio}
\end{figure}"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD8, NEW8, "fig8 → 三张 + 修正图注"),
                          (OLD9, NEW9, "fig9 → 三张")):
        if old in t:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：未命中")

    # 首段导览句：现在共 6 张图
    old_intro = ("Figures~\\ref{fig:weight_svd}--\\ref{fig:adapter_layered} present the full visual "
                 "evidence supporting the Visual Fragility Interpretation.")
    new_intro = ("Figures~\\ref{fig:weight_svd}--\\ref{fig:vision_untouched} give the weight-level "
                 "evidence for the Visual Fragility Interpretation, Figures~\\ref{fig:noise_sensitivity}"
                 "--\\ref{fig:ratio} the parameter-noise probe together with the control that licenses its "
                 "negative result and the comparison that led an earlier version of that claim to be "
                 "withdrawn, and Figures~\\ref{fig:layered_ft}--\\ref{fig:adapter_layered} the layered "
                 "fine-tuning results.")
    if old_intro in t:
        print("  ✅ 导览句已更新（6 张图）")
        if apply:
            t = t.replace(old_intro, new_intro, 1)
        n += 1
    else:
        print("  ⚠ 导览句未命中")

    if apply and n:
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "fig8_weight_svd.png" not in t2 and "fig9_noise_sensitivity.png" not in t2
        for k in ("fig8a_rank_delta.png", "fig8b_budget.png", "fig8c_vision_untouched.png",
                  "fig9a_noise_sweep.png", "fig9b_sigma0_control.png", "fig9c_ratio.png",
                  "fig:budget", "fig:vision_untouched", "fig:sigma0_control", "fig:ratio"):
            assert k in t2, f"断言失败：缺 {k}"
        assert "B--D" not in t2, "旧 fig8 图注的 B--D 仍在"
        print(f"  ✅ 已写入并断言通过（{n} 处）")
    else:
        print(f"\n  {n} 处（{'预演' if not apply else '部分失败'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

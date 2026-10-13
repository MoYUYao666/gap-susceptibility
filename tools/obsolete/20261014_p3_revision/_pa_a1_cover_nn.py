# -*- coding: utf-8 -*-
r"""重写 A1 的 cover letter 以面向 **Neural Networks**（2026-10-10）。

## 现版（`cover_letter.tex`，2026-09-16）哪里不对

| 问题 | 现状 | 应改为 |
|---|---|---|
| **刊名** | `Neurocomputing`（报头/称呼/结尾共 4 处） | **Neural Networks** |
| **标题** | 旧标题 *"The Modality Gap Is **Not** a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness"* | 新标题（**已改**） |
| 🔴 **披露错误** | *"A companion empirical study … is currently **under review at Pattern Recognition** (PR-D-26-10149)"* | **`paper合` 尚未投出**（候选 CVIU/ESWA，状态"待投"）→ **不得声称在审** |
| **卖点** | 未突出"零开销监控"（**新定位的核心**） | 加入 |
| **日期** | 16 September 2026 | 2026-10-10 |
| **缺项** | 未说明曾投他刊 | 按 Elsevier 要求**如实声明** |

**依据**：`docs/PAPERA_VS_COMMENTARY.md` §二（披露三行规定）、
`文件地图.md`（`paper合` = 待投；P1 = PR-D-26-10149 在审）。

    python tools\_pa_a1_cover_nn.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "cover_letter.tex"

NEW = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage[margin=1.1in]{geometry}
\usepackage{parskip}

\begin{document}
\thispagestyle{empty}

\begin{flushright}
Hongrui Wan \\
University of Southampton \\
Southampton, United Kingdom \\
\texttt{contact@example.com}

10 October 2026
\end{flushright}

\vspace{6pt}

\textbf{Re: Submission to \textit{Neural Networks} --- ``Order Preservation as a Zero-Overhead
Monitor for Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health
Metric'' (Regular article)}

\vspace{6pt}

Editor-in-Chief \\
\textit{Neural Networks}

\vspace{12pt}

Dear Editor-in-Chief,

\vspace{6pt}

We are pleased to submit the manuscript ``Order Preservation as a Zero-Overhead Monitor for
Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric'' for
consideration as a regular research article in \textit{Neural Networks}.

\vspace{6pt}

\textbf{Fit with the journal.} The manuscript is a study of learned representations in
contrastively trained dual-encoder neural networks: how the geometry of the joint embedding
space that such a network learns does, and does not, track its classification behaviour, and
how that geometry responds to parameter-efficient adaptation (LoRA) and to full fine-tuning.
Three contrastive vision--language encoders are analysed (CLIP ViT-B/32, OpenCLIP laion2B,
SigLIP base-patch16-224). The contribution is methodological and directly relevant to neural
network learning systems: a controlled intervention on the learned representation (exact
global translations of an embedding cluster, together with a perturbation spectrum), a
first-order analysis of the resulting class-dependent bias field, and an evaluation signal
--- the Kendall order-preservation coefficient of class-relative similarity ranks, $\tau$ ---
that is computable from the top-$k$ class sets a validation pass already produces, and is
therefore available at no additional cost during training. Images and captions enter only as
inputs to the encoders; no image-processing algorithm is proposed or evaluated.

\vspace{6pt}

\textbf{Main findings.} Using controlled ``gap surgery'' replicated across the three model
families, and seventeen fine-tuned checkpoints, we show that zero-shot classification is
governed by the order-preservation coefficient of class-relative similarities and not by gap
magnitude, including regimes in which the two quantities move in opposite directions. A
first-order, class-dependent bias field reproduces the measured per-class scores to four
decimal places ($r=1.000$; this is a self-consistency check of the closed form, not
independent validation) and predicts, as we confirm, that translating the image side destroys
classification while translating the text side does not. We also delineate where the gap
remains the more informative signal: for retrieval-oriented adaptation it is, while for
classification-oriented adaptation $\tau$ is, giving a task-sensitivity ordering (centroid
classification $<$ zero-shot classification $<$ retrieval).

\vspace{6pt}

\textbf{Relation to other manuscripts.} The author is preparing a separate empirical study
(``Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models''),
which is a merged and extended version of two earlier manuscripts and is not yet submitted to
any journal. One of those earlier manuscripts is currently under review at \textit{Pattern
Recognition} (PR-D-26-10149). The present manuscript shares a motivating observation with that
line of work, and cites it as prior work, but is a distinct contribution: the gap-surgery
methodology, the order-preservation analysis, the bias-field theory, and the training-time
monitoring proposal appear here and not in the companion study. The companion study reports
which adaptation position protects cross-modal alignment empirically; the present manuscript
supplies the mechanism, the applicability boundary, and the monitoring signal.

\vspace{6pt}

\textbf{Novelty statement.} To our knowledge this is the first work to (i) give a controlled,
mechanism-level account of how gap changes affect zero-shot classification, (ii) identify order
preservation as the operative quantity, with a bias-field theory verified to four decimal
places and a top-$k$ ablation showing the conclusion does not depend on the choice of $k$, and
(iii) document the image-side/text-side asymmetry of gap manipulation, which reconciles
seemingly conflicting findings in recent literature.

\vspace{6pt}

\textbf{Prior consideration.} This manuscript was previously considered by another journal,
where it was not accepted. It has been revised before the present submission: the title and
abstract have been reframed around the monitoring contribution, and the references have been
reformatted to the style required by \textit{Neural Networks}.

\vspace{6pt}

The manuscript is a single-author submission; the author has no competing interests, as set
out in the accompanying declaration. All data, code, and checkpoints used in this study are
archived and will be released upon publication. We believe \textit{Neural Networks} is the
appropriate venue for this contribution and look forward to your consideration.

\vspace{12pt}

Sincerely,

\vspace{6pt}

Hongrui Wan

\end{document}
"""


def main() -> int:
    apply = "--apply" in sys.argv
    old = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"=== 现版 {len(old.splitlines())} 行 → 新版 {len(NEW.splitlines())} 行 ===")
    for chk, tag in (("Neurocomputing", "旧刊名出现"), ("PR-D-26-10149", "P1 编号"),
                     ("under review at \\textit{Pattern Recognition}", "旧披露口径")):
        print(f"  旧版含「{tag}」: {old.count(chk)} 处")
    if not apply:
        print("\n  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_nc")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(old)
        print(f"  ✅ 备份 {bak.name}")
    io.open(F, "w", encoding="utf-8", newline="").write(NEW)
    t = io.open(F, encoding="utf-8", errors="replace").read()
    assert "Neurocomputing" not in t, "旧刊名未清"
    for k in ("Neural Networks", "Zero-Overhead", "not yet submitted to",
              "PR-D-26-10149", "Prior consideration", "no additional cost"):
        assert k in t, f"断言失败：缺 {k}"
    print("  ✅ cover_letter.tex 已重写（面向 Neural Networks）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""重写 `paper合/cover_letter.tex`（2026-10-11）。

## 旧版（10-02）的 6 处过期/错误

| # | 旧版 | 实际/问题 |
|---|---|---|
| 1 | *"49 pages"* | **56 页** |
| 2 | *"abstract of 238 words"* | **246 词** |
| 3 | *"the ordering tracks the encoder's **patch size** without exception"* | 🔴 **已否证**（同秩对照下 B/16 与 B/32 排序相同）→ 现按**预训练目标**分组 |
| 4 | *"ODE predicts full gap trajectories at mean $R^2=0.986$"* | 论文现写 **0.949**（`0.986` 是别人工作的数字，被误抄） |
| 5 | *"seven strict-freezing configurations"* | 现口径：**三个对比式骨干 + 两个其它目标骨干** |
| 6 | 披露：*"A predecessor manuscript under review at Pattern Recognition (Protect, Don't Perturb…)"* | **那份稿已合并进本文**（P1+P2 = 本文）→ 披露需改写；且 P1 仍投在 PR |

## 新版另加（本轮新发现）

- **数据集翻转**：Flickr30k 上 `text_only` 最保护、MS-COCO 上 `both` 最保护（各 5 seed、同批次）
- **两处理论否证**已写入 limitation（`f(DG_0)` 绝对标定失败；驱动项排序不成立）
- **解码器 VLM**：13 seed，`vision_only` 最弱（分布不重叠）、两强臂不可分辨

    python tools\_pa_cover_rewrite.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "cover_letter.tex"

NEW = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{amsmath}
\pagestyle{empty}
\newcommand{\journal}{[TARGET JOURNAL --- replace before submission]}
\begin{document}

\begin{flushright}
Hongrui Wan \\
\href{mailto:hw4c24@soton.ac.uk}{hw4c24@soton.ac.uk} \\
University of Southampton \\
\today
\end{flushright}

\vspace{1em}

\noindent Dear Editors,

\vspace{0.6em}
\noindent\textbf{Submission of a research article to \emph{\journal}}

\vspace{0.6em}
I am pleased to submit my manuscript ``\emph{Protect, Don't Perturb: From Empirical Regularities to a
Dynamical Theory of Cross-Modal Alignment under PEFT}'' for consideration as a research article in
\emph{\journal}. The manuscript is 56 pages including figures, tables and references, and has not been
published or submitted elsewhere.

\vspace{0.5em}
\noindent\textbf{What the paper does.}
Parameter-efficient fine-tuning of vision-language models is usually evaluated at the level of
retrieval or classification accuracy. This paper instead treats cross-modal alignment as the object of
study and asks how the gap between image and text embeddings evolves during adaptation, and why. It has
three parts. First, an empirical characterisation over $n=204$ archived experiments, in which the
Distribution Gap predicts retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap
($r=-0.59$). Second, a derivation from gradient flow: with the alignment energy as a state variable,
the rate of gap change is the projection of the task gradient onto the alignment gradient, which yields
a first-order ODE whose perturbation force follows from the directional coupling and whose restoring
coefficient is stable within PEFT. Fitted run by run, the ODE reproduces the full gap trajectory at
mean $R^2 = 0.949$ over the LoRA configurations (range $0.814$--$0.977$), against $0.00$ for a constant
baseline. Third, validation across 383 experiments spanning five architectures and three PEFT methods,
including a strict-freezing control in which the optimiser sees only the adapter matrices.

\vspace{0.5em}
\noindent\textbf{Three results I would draw the editor's attention to.}
\emph{(i) The recommended adaptation site is not universal.} The widely reported advantage of adapting
the text side alone holds on the three contrastively pre-trained backbones, where the same arm ordering
recurs at both patch sizes, and \emph{reverses} on SigLIP, a backbone trained with a different
objective. Patch size is not what separates them: measured at the same rank under one protocol, CLIP
B/16 and CLIP B/32 order the arms identically. The ordering follows the pre-training objective, and the
paper derives the mechanism that produces it.
\emph{(ii) The best site depends on the corpus as well as the architecture.} Under the same
strict-freezing protocol at rank $4$, text-only holds the gap best on Flickr30k
($-0.0304\pm0.0039$ against $-0.0204\pm0.0028$ for both positions), whereas on MS-COCO both positions
hold it best ($-0.0877\pm0.0022$ against $-0.0430\pm0.0028$), five seeds per arm at one batch size. A
recommendation therefore has to be established per corpus and per backbone rather than assumed.
\emph{(iii) A marker of what the theory does not yet do.} Two of its quantitative claims are falsified
by direct measurement --- the absolute value of the restoring coefficient disagrees in sign with the
fitted one, and the trajectory-averaged driving term does not reproduce the arm ordering --- and both
are reported as limitations rather than smoothed over. What survives is the per-step gradient identity,
verified against the change an actual optimiser step produces, and the sign and rough magnitude of the
coefficient.

\vspace{0.5em}
\noindent\textbf{Relation to prior work, stated explicitly.}
Individual studies have argued that the choice of adaptation site outweighs how a fixed budget is
divided within it in the low-data regime, and report gains from siting adaptation so that the vision
tower is left unchanged rather than from re-allocating rank among its modules \cite{zhang2023adalora,wang2024loraga,zanella2024cliplora}. Those reports establish that the choice matters; they do not
establish how far the resulting ordering generalises, because each is measured on a single backbone and
a single corpus. The present manuscript treats the ordering as a hypothesis rather than a premise and
measures the same three arms on five backbones under one protocol.

\vspace{0.5em}
\noindent\textbf{Related manuscripts by the same author, disclosed.}
Three related items by the same author are in the editorial process or in preparation, and I disclose
them so that the editor can judge overlap directly rather than infer it:
\begin{itemize}\itemsep0.25em
\item \textbf{A predecessor manuscript} under review at \emph{Pattern Recognition} (``Protect, Don't
Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models''). That manuscript covers the
empirical characterisation only. The present submission \emph{supersedes} it: it adds the dynamical
theory, the cross-architecture validation and the strict-freezing controls, and it is the fuller
treatment of the same programme of work. The predecessor's empirical material appears here in merged
and extended form, and readers should treat this manuscript as the current version.
\item \textbf{A critical review} under review at \emph{Pattern Recognition Letters} (``Allocation, not
selection: comparability in parameter-efficient multimodal adaptation''), now at manuscript number
\texttt{PRLETTERS-D-26-02378}. That is a survey of published literature with a reporting checklist as
its output; it reports no experiments of its own. It shares one conclusion with the present manuscript
--- that the adaptation site dominates the division of budget --- which it reaches by generalising over
published work, whereas the present manuscript reaches it by direct measurement.
\item A manuscript on an unrelated topic (underwater acoustics) under review at \emph{IEEE Journal of
Oceanic Engineering} (\texttt{26-0663}).
\end{itemize}
The present manuscript is not under consideration elsewhere, and no part of it has been published.

\vspace{0.5em}
\noindent\textbf{Reproducibility and data.}
Every number reported derives from an archived result file produced by a named script. All runs use a
single batch size and five seeds per configuration (thirteen for the decoder-model control), and the
manuscript's tables are checked against the archive by an automated audit that recomputes each entry.
One caveat is stated in the manuscript: the quantised (four-bit) configuration of the decoder-model
pipeline is not bit-reproducible, which is why those results are reported in bfloat16. The result files
and scripts are available to the editors and reviewers on request and will be made public on
publication.

\vspace{0.5em}
\noindent\textbf{Compliance.}
The manuscript provides highlights (five items, longest 61 characters), an abstract of 246 words, six
keywords, a data availability statement, a funding statement, a declaration of competing interests, a
CRediT authorship contribution statement, and a declaration of generative AI use in manuscript
preparation.

\vspace{0.8em}
\noindent Thank you for considering this submission.

\vspace{1.2em}
\noindent Yours sincerely,

\vspace{1.4em}
\noindent Hongrui Wan \\
University of Southampton

\end{document}
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    old = io.open(F, encoding="utf-8", errors="replace").read()
    bak = F.with_suffix(".tex.bak_pre1011")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(old)
    io.open(F, "w", encoding="utf-8", newline="").write(NEW)
    t = io.open(F, encoding="utf-8", errors="replace").read()
    for k in ("56 pages", "246 words", "mean $R^2 = 0.949$",
              "The ordering follows the pre-training objective",
              "supersedes", "PRLETTERS-D-26-02378", "26-0663",
              "not bit-reproducible", r"$-0.0877\pm0.0022$"):
        assert k in t, f"断言失败：缺 {k}"
    for k in ("49 pages", "238 words", "0.986$", "patch size without exception"):
        assert k not in t, f"旧内容仍在: {k}"
    print("  ✅ cover_letter.tex 已重写（旧版备份 .bak_pre1011）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

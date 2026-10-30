# -*- coding: utf-8 -*-
r"""重写 cover letter（Revise 版）+ highlights + title page，全部对齐已修订的稿件（2026-10-14）。

## 为什么要重写（不是小改）

| 文案 | 现含 | 稿件现况 |
|---|---|---|
| **cover letter** | *"the **unique** scalar satisfying five requirements"* | 需**额外假设 R3$'$**（有反例） |
| | *"an alignment-energy **phase transition with a critical rank**"* | **降级为 bracketed**，且属协议 |
| | *"random allocation suffers a **$30\\times$** larger sd"* | **已撤回**（$\\eta^2=0.989$） |
| | *"**190 runs** (181 sweep + 9)"* | **126 + 57 runs** |
| | *"which we attribute to **architectural differences**"* | **已撤回**（token 预算伪影） |
| | 无篇幅说明 | Guide 要求 ≤7 页，本稿 10 页 ⇒ **须主动说明** |
| | 无数据可用性 | Guide **Option C**：deposit + 引用链接 |
| **highlights** | *"the **unique** admissible allocation statistic"* | 同上 |
| | *"A **critical rank** separates safe, damaging and collapsing regimes"* | 同上 |
| | *"predicts allocation **uncertainty**"* | **已撤回** |

**⇒ 三件全部重写，并按 Guide 补"篇幅说明"与"数据可用性"。**

    python tools\_p562_rewrite_cover_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

COVER = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\pagestyle{empty}
\begin{document}

\begin{flushright}
Hongrui Wan \\
hw4c24@soton.ac.uk \\
University of Southampton \\
\today
\end{flushright}

\vspace{1em}

Prof.\ Editor-in-Chief \\
\emph{Pattern Recognition Letters}

\vspace{1em}

Dear Editor,

\textbf{Revised submission (research report) to \emph{Pattern Recognition Letters}}

I am pleased to submit the revised version of my manuscript ``\emph{Gradient Structure Laws as
Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}'' (original submission
\texttt{PRLETTERS-D-26-02378}). I am grateful to the reviewers: acting on their reports changed
the paper's claims, and in four places the change is \emph{against} what I originally wrote. I
summarise those reversals here rather than leaving them to be discovered in the response letter.

\vspace{0.5em}
\textbf{What the paper does.} Parameter-efficient fine-tuning of vision--language models requires
a decision that is usually made empirically: how to distribute a fixed adapter-rank budget across
a network's blocks. The paper asks whether that decision can be made \emph{before} training, from
the source model alone. The central object is the cross-modal gradient coupling
$\Gamma_k = \langle \nabla_{M_k}E, u_{M_k}\rangle$. We show that under the requirements the
problem imposes, together with an additivity assumption we now state explicitly rather than
derive, $\Gamma$ is the canonical statistic up to positive scaling, and that constrained
optimisation gives an exponential allocation. The transfer we report is
encoder-only to decoder-based: $\Gamma$ measured on CLIP predicts a rank allocation for LLaVA
instruction tuning with no target-model gradient entering the decision.

\vspace{0.5em}
\textbf{What changed in revision.} (1) \emph{A gap in the proof, found by Reviewer~1}: block
decomposability does not imply bilinearity, so the Representation Theorem's uniqueness claim was
not established as stated. We have added the missing property as an explicit axiom (R3$'$) and
proved that it does not follow from the earlier requirements, with a counterexample. (2) \emph{The
allocation comparison, run as Reviewer~2 asked}: the $\Gamma$-guided allocation now exists as a
true block-wise experiment at an identical trainable-parameter count, and it does \emph{not}
survive our own controls --- it reverses at another learning rate and disappears once the arms are
matched on training loss. We have withdrawn the claim that it beats the uniform baseline.
(3) \emph{AdaLoRA, at matched budget and swept over the same learning rates, reaches lower
alignment energy than any of our arms}, and the paper now says so. (4) \emph{The "sharp phase
transition" is downgraded to a crossing bracketed by two ranks}, and the "architecture-dependent"
reading is withdrawn: that contrast tracked the visual token budget. (5) A downstream check we ran
(CLIP retrieval on real Flickr30k pairs) shows that lowering the alignment energy does not
reliably improve retrieval, so the paper now presents $E$ as a diagnostic of representation
geometry rather than a proxy for task accuracy. What survives is a narrower and, we think, more
useful claim: the rule allocates \emph{without searching}, and where a search is affordable an
adaptive method should be preferred.

\vspace{0.5em}
\textbf{Why \emph{Pattern Recognition Letters}.} The contribution is a concise methodological
result with a transferable prediction, which matches the Journal's stated aim, and it sits in its
subject areas of machine learning and computer vision. The negative results above are reported in
full because they bound the method's scope.

\vspace{0.5em}
\textbf{Length.} The Guide for Authors specifies a two-column manuscript of no more than seven
pages including all material. The original submission was eleven pages and entered review; this
revision is \textbf{ten pages} in two-column format, with the axiom derivation, full proofs,
protocol details, per-run tables and additional figures moved to Supplementary Material. I would
rather flag this than have it surface at production, and I am happy to compress further if the
Editor prefers.

\vspace{0.5em}
\textbf{Data and code availability (Guide, Option~C).} All datasets and pre-trained models used are
public (Alpaca, ShareGPT, MS-COCO, Flickr30k, an ImageNet subset; CLIP ViT-B/32, LLaVA-1.5-7B,
Qwen2-VL-7B/2B). The derived data this paper relies on --- per-run result records, the analysis
scripts that compute every reported statistic, and the training configurations --- are archived at
\texttt{[REPOSITORY DOI, to be inserted]} and are available to the editor and reviewers now. Every
number in the manuscript can be recomputed from the public resources above; no non-public data is
required.

\vspace{0.5em}
\textbf{Prior submission history (disclosed for transparency).} An earlier, differently scoped
version of this manuscript was submitted to \emph{IEEE Transactions on Neural Networks and
Learning Systems} (manuscript \mbox{TNNLS-2026-P-50569}) and was rejected on 3 September 2026. No
part of the present manuscript is under consideration elsewhere, and it has not been published
previously in any form.

\vspace{0.5em}
\textbf{Declarations.} Single-author submission; the author declares no competing interests.
Generative AI tools (Claude, DeepSeek) were used to draft and revise the manuscript text and to
prepare experimental code and figures; the author reviewed and edited all content and takes full
responsibility for it, as declared in the manuscript.

\vspace{0.5em}
I would be glad to provide any further information the editorial office requires, and I thank the
reviewers again for reports that materially improved the paper.

\vspace{1em}

Sincerely,

\vspace{1em}

Hongrui Wan \\
University of Southampton \\
\href{mailto:hw4c24@soton.ac.uk}{hw4c24@soton.ac.uk}

\end{document}
"""

HIGHLIGHTS = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\pagestyle{empty}
\begin{document}

\begin{center}
{\large\bfseries Highlights}
\end{center}

\vspace{0.5em}

\noindent\textit{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation}\\
Hongrui Wan --- University of Southampton

\vspace{1em}

\begin{itemize}[leftmargin=1.5em,itemsep=0.5em]
  \item Cross-modal gradient coupling gives a canonical PEFT allocation statistic
  \item Requiring additivity is an explicit axiom, not a consequence of block decomposability
  \item Measured on CLIP, it predicts a LLaVA rank allocation with no target-model gradient
  \item The allocation does not beat matched controls; we report that rather than hide it
  \item At matched budget, AdaLoRA reaches lower alignment energy than our allocation
\end{itemize}

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    # 检查 highlights 每条 ≤85 字符（Guide 要求）
    import re
    items = re.findall(r"\\item (.+)", HIGHLIGHTS)
    print("  highlights 各条长度（Guide 上限 85 字符）：")
    ok = True
    for it in items:
        n = len(it)
        flag = "✅" if n <= 85 else "🔴"
        ok = ok and n <= 85
        print(f"     {flag} {n:>3} 字符  {it}")
    print()
    target = [("cover_letter_prl.tex", COVER), ("PRL_submission/highlights.tex", HIGHLIGHTS)]
    for rel, new in target:
        p = PI / rel
        old = io.open(p, encoding="utf-8", errors="replace").read() if p.exists() else ""
        print(f"  {rel:<38} {len(old):>6,} → {len(new):>6,} 字符")
    if not a.apply:
        print("  （预演）")
        return 0
    for rel, new in target:
        p = PI / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        bak = p.with_suffix(p.suffix + ".bak_p562")
        if p.exists() and not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(new)
    # 复核：禁止回归的旧主张
    print()
    print("  复核（cover letter 与 highlights 不应含）：")
    allt = COVER + HIGHLIGHTS
    for bad, label in (("the unique scalar", "unique 主张"),
                       ("phase transition with a critical rank", "sharp 相变"),
                       ("A critical rank separates", "critical rank 分隔"),
                       ("190 runs", "旧计数"),
                       ("30\\times", "30× 主张"),
                       ("architectural differences", "架构差异主张"),
                       ("allocation uncertainty", "不确定性主张")):
        n = allt.count(bad)
        ok = ok and n == 0
        print(f"  {'✅' if n == 0 else '🔴'} {label}: {n} 处")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""Rewrite the S17 claim table so every row reflects the current evidence (no stale 'untested' rows)."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")

rows = r"""
$\Gamma$ is the unique admissible additive statistic given (R3$'$) & supported & Theorem 1; (R3$'$) used as an assumption \\
block additivity (R3$'$) for the probe & supported for the probe & pair residuals below $0.12\%$, CIs near zero (S30); general case untested \\
cross-architecture $\Gamma$ predicts the LLaVA rank ordering & supported & C4; transfer controls \\
alignment-energy crossing on the blank-image protocol & supported & five seeds, exact $p=0.008$; ten seeds $r=3$--$8$ completely separated, $p\approx1.1\times10^{-5}$ (S33) \\
crossing position reproducible with ten seeds & supported & complete separation (S33) \\
crossing pattern repeats on a second instruction family & supported for Dolly-15k & $r=4/5$ negative, $r=6/7$ positive (S40) \\
zero-shot allocation beats uniform rank & \emph{not} supported & trained arms $+196$ to $+444$; official IGU arm $+240.5$ (S19, S27, S39) \\
NTK/IGU/HALoRA/Shap allocation improves the energy & \emph{not} supported & NTK $+396.0$, $\Gamma$ $+196.5$, official IGU $+240.5$ (S19, S27, S39) \\
signed $\Gamma$ or a non-CLIP source improves the ordering & reported, no positive claim & S32 tables \\
crossing generalises to real image--text pairs & \emph{not} supported & multi-seed caption protocol, all ranks positive (S35) \\
energy predicts caption quality & \emph{not} supported & null caption check (S21) \\
energy predicts instruction-following quality & reported, no positive claim & instruction check (S25) \\
energy predicts VQA accuracy & reported, no positive claim & 1434 training pairs, 300 held-out questions (S28) \\
$\Gamma$ insensitive to the reference batch & \emph{not} supported & CV 0.32--0.55; bootstrap allocation reproduced in 23\% of draws (S23, S38) \\
crossing stable across torch/CUDA versions & \emph{not} supported & $r=6$ positive everywhere; $r=5$ shifts with the stack (mean $-23$/$-44$/$+34$; S29, S37) \\
curvature sign stable across ranks, seeds and stacks & \emph{not} supported & share below $0.6\%$ at the operating step, sign varies (S34) \\
first-order truncation adequate at the operating step & supported locally & second-order share below $0.6\%$ at $\eta=5\times10^{-5}$ (S34) \\
second-order term negligible on Qwen2-VL-2B & supported & share below $1\%$ at the operating step (S18) \\
non-finite energy is an optimizer blow-up & \emph{not} supported & 17/17 runs: loss finite while energy non-finite (S24) \\
crossing transfers to a newer model family & \emph{not} supported & Qwen2.5-VL-3B (no sign change) and 7B (both ranks negative) (S20) \\
crossing transfers to a third checkpoint family & \emph{not} supported & Qwen2-VL-2B: both ranks $-384$ (S41) \\
AdaLoRA is worse than our arms & \emph{not} supported & AdaLoRA reaches lower energy in our comparison \\
official IGU allocation ported and trained & reported, no positive claim & official code + name adapter, arm $+240.5$ (S39) \\
""".strip("\n")

new_sec = (r"""\section{Assumption audit and claim status}
\label{app:claims}

Table~\ref{tab:claims} separates what this paper supports from what it does not. It is the compact form of the evidence
discussion: an assumption is listed where the claim depends on it, and every ``not supported'' row names the control that
bounds the claim.

\begin{table*}[h]
\centering
\footnotesize
\caption{Claim status. ``Supported'' means the stated scope is backed by the cited evidence; ``not supported'' means the
paper's own controls contradict or do not establish the claim.}
\label{tab:claims}
\begin{tabular}{@{}p{0.40\textwidth}p{0.13\textwidth}p{0.40\textwidth}@{}}
\toprule
claim & status & evidence / bound \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\end{table*}""")

t = io.open(SUPP, encoding="utf-8").read()
head = "\\section{Assumption audit and claim status}"
start = t.find(head)
assert start >= 0
nxt = t.find("\\section{", start + len(head))
end = nxt if nxt >= 0 else t.find("\\bibliographystyle", start)
t = t[:start] + new_sec + "\n" + t[end:]
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S17 rewritten with %d rows" % (rows.count("\\\\") + 1))

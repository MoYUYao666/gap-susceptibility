# -*- coding: utf-8 -*-
r"""Beautify Table 10 (`tab:decoderladder`, the matched objective ladder) the way a journal table should read:

  - caption cut from ~940 to ~2.5 lines; the protocol detail and the sign-convention explanation move into a
    table note below the rules, where they belong;
  - numeric columns right-aligned;
  - column headers carry units and the sign convention;
  - rows grouped by backbone with `\cmidrule` so the 2x2 objective design is visible at a glance.

Only presentation changes: every number and every claim is preserved verbatim.
"""
import io
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = "paper合/reframed/sections/95_appendix_original.tex"
t = io.open(P, encoding="utf-8").read()

OLD_START = "\\begin{table}[!htbp]\n\\centering\n\\caption{The matched objective ladder."
i = t.find(OLD_START)
assert i >= 0, "Table 10 block not found"
j = t.find("\\end{table}", i) + len("\\end{table}")

NEW = r"""\begin{table}[!htbp]
\centering
\caption{The matched objective ladder: the same training protocol run under a contrastive or a generation
objective, for two backbones (plus one larger generation-only control). Frozen is the untrained model, final
is the third epoch; the change is the archive's \texttt{delta\_DG\_percent}, so a negative entry means the gap
narrowed.}
\label{tab:decoderladder}
\footnotesize
\begin{tabular}{l l r r r}
\toprule
Backbone & Objective & Frozen $DG^*$ & Final $DG^*$ & Change (\%) \\
\midrule
\multirow{2}{*}{Qwen2-VL-2B}
  & Contrastive & $0.6445$ & $0.0723$ & $-88.8$ \\
  & Generation  & $0.6445$ & $0.6211$ & $-3.6$  \\
\cmidrule(lr){2-5}
\multirow{2}{*}{LLaVA-1.5-7B}
  & Contrastive & $0.4819$ & $0.1683$ & $-65.1$ \\
  & Generation  & $0.4558$ & $0.5293$ & $+16.1$ \\
\cmidrule(lr){1-5}
Qwen2.5-VL-7B & Generation & $1.0781$ & $0.7070$ & $-34.4$ \\
\bottomrule
\end{tabular}

\vspace{2pt}
{\footnotesize
\emph{Notes.} One protocol for all five runs (\texttt{meta.protocol} $=$ \texttt{match}): $320$ image--caption
pairs from \texttt{data/marine\_captions}, three epochs, LoRA rank $8$, $\alpha=16$, the both-position arm,
seed $42$, four-bit nf4; the Qwen runs at batch $4$ with the image side capped at $196$ tokens, LLaVA-1.5-7B at
batch $2$ with its fixed $576$-token splice. $DG^*$ is the paired squared distance after $L_2$ normalisation
(image-token pool against caption pool, no projection) on the whole evaluation set, rounded to four decimals;
the change is rounded to one. The sign convention is the archive's: a negative change means the gap narrowed,
whereas Tables~\ref{tab:vlm} and~\ref{tab:llava} print the reduction with the opposite glyph for the same
direction.}
\end{table}"""

t = t[:i] + NEW + t[j:]
# multirow is already loaded in the ML preamble; the reframed elsarticle preamble also loads it -- assert
io.open(P, "w", encoding="utf-8", newline="").write(t)
print("Table 10 rebuilt: short caption, grouped rows, right-aligned numerics, units and sign convention in the note")

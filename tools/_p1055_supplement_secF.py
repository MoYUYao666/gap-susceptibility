# -*- coding: utf-8 -*-
r"""Add Section F to Paper A's supplement: the LLaVA-1.5-7B bfloat16 campaign as a scoped negative result.

Operator decision 2026-10-16 (option 1): report it under cross-model tension / limitations, not as evidence
for or against the thesis.

What the section says, and why each part is there:

* the protocol and the four arms, with the measured changes and their seed spread;
* the **null result stated plainly**: text-only does not move this metric (identical to frozen bit for bit),
  which is the opposite of the direction the paper's Qwen2-VL-2B comparison reports;
* the **reason it is not treated as evidence against the thesis**: this pipeline measures a different DG*
  (mean pairwise distance minus within-modality distances) from the archived variance-based one
  (`src/gap_metrics.py`: W2 = sqrt(CG^2 + ||sigma_I - sigma_T||^2)), and its text side is the language
  model's token embedding rather than an independent text encoder. The magnitudes differ accordingly
  (starting DG* 0.26 here against 0.64-2.18 there), so the two are not the same quantity;
* the **limit of resolution**: frozen advances 0.261161 -> 0.261937 over its epochs while training nothing,
  so a change of that size is not interpretable here;
* what would settle it: re-run under the archived metric definition, which needs more device memory than the
  32 GB used.

    python tools/_p1055_supplement_secF.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper合" / "sections" / "supplement.tex"
MARK = "F. A Larger Decoder Model"

SECTION = r"""

\section*{F. A Larger Decoder Model: A Scoped Null Result}
\label{sec:llava}

Section~\ref{sec:vlm} reports a decoder-based VLM with $2$B parameters. To see whether that picture extends
to a larger decoder model we repeated the strict-freezing comparison on LLaVA-1.5-7B \cite{liu2023llava} in
bfloat16, at $1500$ training pairs and $500$ held-out pairs, three epochs, batch $2$, rank $8$ and learning
rate $10^{-4}$, with three seeds per arm. The twelve runs are archived as
\texttt{outputs/llava\_bf16\_sites\_cloud/}, one file per arm and seed, together with the summary the sweep
wrote. We report this as a negative result with an explicit scope, because the quantity we could measure on
this model is not the quantity the rest of the paper measures.

The measured changes are shown in Table~\ref{tab:llava}. The direction agrees with the strict-freezing result
that the vision side is where intervention moves the gap: adapting the vision side and the projector alone
raises $DG^*$ by $13.33\%$ on average, with a seed spread of $4.74$ points (individual seeds $+7.53\%$,
$+13.33\%$ and $+19.14\%$), and covering both sides raises it by $6.07\%$ with a spread of $6.55$ points. What
does not carry over is the protective behaviour of text-only adaptation. On this model the text-only arm
returns \emph{exactly} the frozen value at every seed: $0.2619372457265854$ in all six runs, bit for bit. The
text arm trains $19{,}988{,}480$ parameters against $0$ for frozen, and the training loss falls from $1.55$ to
$0.39$ over three epochs, so the adapter is not inert; it simply does not move this metric.

\begin{table}[h]
\centering
\caption{Strict freezing on a larger decoder VLM. LLaVA-1.5-7B, $1500$ training pairs, three epochs, batch
$2$, rank $8$, bfloat16, three seeds per arm. $DG^*$ here is the mean pairwise distance minus the mean
within-modality distance, which differs from the variance-based definition used elsewhere in this paper (see
the text); the values are therefore not comparable with Table~\ref{tab:vlm}. Starting values are shared
across arms because every arm starts from the same frozen backbone.}
\label{tab:llava}
\footnotesize
\begin{tabular}{lcc}
\hline
Arm & Trainable & $\Delta DG^*$ (\% of own start) \\
\hline
Frozen      & $0$          & $+0.297 \pm 0.000$ \\
Text-only   & $19{,}988{,}480$ & $+0.297 \pm 0.000$ \\
Vision-only & $3{,}645{,}440$  & $+13.333 \pm 4.737$ \\
Both        & $23{,}633{,}920$ & $+6.068 \pm 6.547$ \\
\hline
\end{tabular}
\end{table}

Two features of the run bound how far it can be read. First, the starting $DG^*$ is $0.261161$ and the frozen
arm reaches $0.261937$ after three epochs of no training at all, so the scale on which the text-only arm
"does nothing" is a change of $0.0008$; with three seeds that all coincide, this pipeline cannot resolve
effects at the scale the paper's comparisons rely on. Second, and more importantly, the quantity differs from
the archived one. The paper's empirical $DG^*$ is variance-based, $W_2^2 = \|\mu_I - \mu_T\|^2 +
\|\sigma_I - \sigma_T\|^2$ (\texttt{src/gap\_metrics.py}), whereas the decoder pipeline we could run on a
single $32$\,GB device forms the gap from the mean pairwise cross-modal distance and the two within-modality
distances, and takes its text side from the language model's token embedding rather than from an independent
text encoder. The magnitudes reflect that: the starting $DG^*$ is $0.26$ here against $0.64$ to $2.18$ across
the arms of Table~\ref{tab:vlm}. A null on one is therefore not a null on the other, and we do not present
this model as contradicting Section~\ref{sec:vlm}.

What would settle the question is a run of the same model under the archived metric definition, which requires
more device memory than was available: the 7B model in bfloat16 needs about $30$\,GB before activations, and
the archived definition additionally requires an independent text embedding for the captions. We record the
protocol, the archive and this limitation so that the comparison can be completed when such a device is
available, rather than leaving the question implicit.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SUPP.read_text(encoding="utf-8")
    if MARK in t:
        print("  already present")
        return 0
    # `sections/supplement.tex` is a fragment included by \input (no \end{document}), so the section is
    # appended at the end of the file.
    out = t.rstrip("\n") + "\n" + SECTION
    assert out.count("\\begin{table}") == out.count("\\end{table}"), "table environment unbalanced"
    assert out.count("$") % 2 == 0, "unbalanced math delimiters"
    assert out.count("{") == out.count("}"), "unbalanced braces"
    print(f"  section F added ({len(SECTION.splitlines())} lines); braced/math/table checks pass")
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

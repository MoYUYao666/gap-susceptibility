# -*- coding: utf-8 -*-
r"""Re-typeset the configuration-comparison table: 3 columns, ragged-right cells, same heading style as section A.

The 4-column version was legible but ugly -- narrow justified `p` columns hyphenated words ("Sec-tion I") and stretched
the inter-word spaces, and the float was pushed to the next page, separating it from its heading. This pass keeps the
same facts in three columns, sets the cells ragged-right, and uses `\section*` so the heading matches the catalogue's.

    python tools/_p1187_retable_config.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

NEW = r"""\section*{A.1 Configuration groups: why apparently similar runs report different numbers}

The catalogued runs fall into four groups that differ not only in hyperparameters but in what is adapted and how; several
rounds of the analysis treat one group as if it were another, so they are set side by side here. Every entry is read from
the archived per-run records named in the caption.

\begin{table}[h!]
\centering
\caption{The four configuration groups behind the paper's numbers. ``Settings'' gives the nominal configuration;
``what separates it'' is why a number from one group cannot be substituted for another. Core entries from
\texttt{outputs/flickr30k/alpha\_*/results.json}, Route D entries from \texttt{outputs/route\_d/*/results.json}.}
\label{tab:config_groups}
\scriptsize
\renewcommand{\arraystretch}{1.02}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.15\textwidth}>{\raggedright\arraybackslash}p{0.20\textwidth}>{\raggedright\arraybackslash}p{0.55\textwidth}@{}}
\toprule
Group & Settings & What separates it \\
\midrule
Core LoRA, Section~I (30 runs) &
$r=8$, $\alpha\in\{4,\dots,64\}$, one run per $\alpha$ &
Batch 128, 10 epochs, AdamW $10^{-4}$. Larger $\alpha$ lowers the gap monotonically, from $-0.017$ at $\alpha=4$ to
$-0.081$ at $\alpha=64$, with validation loss $0.50$--$0.54$ throughout. \\
\addlinespace
Route D combinations (5 runs) &
fixed $\alpha=64$; $r\in\{4,8,16\}$; \texttt{qv} or \texttt{qvko}; one run each &
Not the core configuration: $r=4$ gives $+0.183$, \texttt{qvko} $+0.164$, Gap-Init $+0.188$, $r=16$ $+0.196$. Its only
$r=8$ member has validation loss $2.33$ against $0.50$ and $R@1=0.389$, so its $+0.079$ is a degenerate fit, withdrawn
rather than compared. \\
\addlinespace
Layered unfreezing (appendix) &
text tower plus the first $k$ vision layers, $k$ swept &
A different intervention: there is no vision-only or both-position arm, and the reference is the frozen model, so these
numbers are not comparable with Table~\ref{tab:position}. \\
\addlinespace
Strict freezing, controls (104 runs) &
adapter matrices only; vision tower frozen by construction; $r\in\{1,\dots,64\}$; 3--6 seeds &
The arms differ only in where the adapters sit, which is why the position findings rest on this group. $98{,}304$
(text-only) or $491{,}520$ (both-position) trainable parameters at $r=8$. \\
\bottomrule
\end{tabular}
\end{table}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8").read()
    start = t.find("\\section*{A.1 Configuration groups")
    if start < 0:
        start = t.find("\\subsection*{A.1 Configuration groups")
    if start < 0:
        print("  !! A.1 block not found")
        return 1
    end = t.find("\\FloatBarrier", start)
    if end < 0:
        print("  !! FloatBarrier not found")
        return 1
    end += len("\\FloatBarrier")
    print(f"  replacing {end-start} chars")
    print("  checks: label=%s raggedright=%s rows=%d" %
          ("label{tab:config_groups}" in NEW, "raggedright" in NEW, NEW.count("\\\\\n\\addlinespace") + 1))
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUP, "w", encoding="utf-8", newline="").write(t[:start] + NEW + t[end:])
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

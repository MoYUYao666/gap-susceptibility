# -*- coding: utf-8 -*-
r"""Final typesetting of the configuration table: parbox cells with ragged-right text.

Two attempts failed for package reasons (`array` is not loaded, so `>{\raggedright\arraybackslash}p{}` is illegal) and
the plain `p` columns justify their text, which stretches the narrow first two columns badly. Wrapping each cell in
`\parbox[t]{...}{\raggedright ...}` inside ordinary `l` columns needs no package and gives ragged-right text with the
intended widths. Facts and numbers are unchanged.

    python tools/_p1189_table_parbox.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

NEW = r"""\begin{table}[h!]
\centering
\caption{The four configuration groups behind the paper's numbers. ``Settings'' gives the nominal configuration;
``what separates it'' is why a number from one group cannot be substituted for another. Core entries from
\texttt{outputs/flickr30k/alpha\_*/results.json}, Route D entries from \texttt{outputs/route\_d/*/results.json}.}
\label{tab:config_groups}
\scriptsize
\renewcommand{\arraystretch}{1.0}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}l@{\hspace{6pt}}l@{\hspace{6pt}}l@{}}
\toprule
Group & Settings & What separates it \\
\midrule
\parbox[t]{0.155\textwidth}{\raggedright Core LoRA, Section~I (30 runs)} &
\parbox[t]{0.185\textwidth}{\raggedright $r=8$, $\alpha\in\{4,\dots,64\}$, one run per $\alpha$} &
\parbox[t]{0.545\textwidth}{\raggedright Batch 128, 10 epochs, AdamW $10^{-4}$. Larger $\alpha$ lowers the gap
monotonically, from $-0.017$ at $\alpha=4$ to $-0.081$ at $\alpha=64$, with validation loss $0.50$--$0.54$
throughout.} \\
\addlinespace[3pt]
\parbox[t]{0.155\textwidth}{\raggedright Route D combinations (5 runs)} &
\parbox[t]{0.185\textwidth}{\raggedright fixed $\alpha=64$; $r\in\{4,8,16\}$; \texttt{qv} or \texttt{qvko}; one run each} &
\parbox[t]{0.545\textwidth}{\raggedright Not the core configuration: $r=4$ gives $+0.183$, \texttt{qvko} $+0.164$,
Gap-Init $+0.188$, $r=16$ $+0.196$. Its only $r=8$ member has validation loss $2.33$ against $0.50$ and
$R@1=0.389$, so its $+0.079$ is a degenerate fit, withdrawn rather than compared.} \\
\addlinespace[3pt]
\parbox[t]{0.155\textwidth}{\raggedright Layered unfreezing (appendix)} &
\parbox[t]{0.185\textwidth}{\raggedright text tower plus the first $k$ vision layers, $k$ swept} &
\parbox[t]{0.545\textwidth}{\raggedright A different intervention: there is no vision-only or both-position arm, and
the reference is the frozen model, so these numbers are not comparable with Table~\ref{tab:position}.} \\
\addlinespace[3pt]
\parbox[t]{0.155\textwidth}{\raggedright Strict freezing, controls (104 runs)} &
\parbox[t]{0.185\textwidth}{\raggedright adapter matrices only; vision tower frozen by construction;
$r\in\{1,\dots,64\}$; 3--6 seeds} &
\parbox[t]{0.545\textwidth}{\raggedright The arms differ only in where the adapters sit, which is why the position
findings rest on this group. $98{,}304$ (text-only) or $491{,}520$ (both-position) trainable parameters at
$r=8$.} \\
\bottomrule
\end{tabular}
\end{table}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8").read()
    start = t.find("\\begin{table}[h!]", t.find("label{tab:config_groups}") - 400)
    # locate the table that carries the config_groups label
    lab = t.find("label{tab:config_groups}")
    start = t.rfind("\\begin{table}", 0, lab)
    end = t.find("\\end{table}", lab) + len("\\end{table}")
    if start < 0 or end < len("\\end{table}"):
        print("  !! table block not found")
        return 1
    print(f"  replacing {end-start} chars")
    checks = [
        ("parbox cells", NEW.count("\\parbox") == 12),
        ("raggedright present", NEW.count("\\raggedright") == 12),
        ("label intact", "label{tab:config_groups}" in NEW),
        ("no array syntax", "arraybackslash" not in NEW),
    ]
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not all(ok for _, ok in checks):
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUP, "w", encoding="utf-8", newline="").write(t[:start] + NEW + t[end:])
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

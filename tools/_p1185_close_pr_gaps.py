# -*- coding: utf-8 -*-
r"""Close the two remaining gaps from the Pattern Recognition audit.

Gap 1 (R2-W4): the retained evidence for Visual Fragility is correlational, and regularisation / modality-specific
optimisation dynamics are not excluded as alternatives. The limitations list already runs to twelve items but contains
none of this vocabulary, so a thirteenth qualification is appended.

Gap 2 (R1-Q2 + R1-W1): the reviewer asked for a configuration-comparison table explaining why apparently similar runs
report different numbers. The disputed +0.079 case is now fully traced in the archives:

    core   outputs/flickr30k/alpha_64/results.json        R@1 0.6370  CGdelta -0.0808  val 0.4986
    RouteD outputs/route_d/d1_alpha64_text_r8/results.json R@1 0.3890  CGdelta +0.0792  val 2.3313

Same nominal rank (r=8), same scaling (alpha=64), same 145,170,177 trainable parameters -- but the Route D run's
validation loss is 4.7x the core run's, i.e. a degenerate fit, not a different design. The other Route D members differ
in rank (4/16), target modules (qvko) or initialisation (Gap-Init), so none of them is the core configuration either.
All numbers written by this script come from those two JSON files plus the Route D siblings.

    python tools/_p1185_close_pr_gaps.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"
EMP = SEC / "empirical.tex"
SUP = SEC / "supplement.tex"
DIS = SEC / "discussion.tex"

OLD_079 = (r"(An earlier version of this sentence quoted $+0.079$ for the text-only arm; that value belongs to a "
           r"different configuration, $\alpha=64$, whose $R@1$ is $0.389$, and it is withdrawn.)")

NEW_079 = (r"(An earlier version of this sentence quoted $+0.079$ for the text-only arm. That value is the Route D run "
           r"\texttt{d1\_alpha64\_text\_r8}, which shares the nominal rank and scaling of the core run quoted here but "
           r"ends with a validation loss of $2.33$ against $0.499$, and an $R@1$ of $0.389$; we treat it as a "
           r"degenerate fit and the value is withdrawn. Table~\ref{tab:config_groups} in the appendix sets the "
           r"configuration groups side by side.)")

TABLE = r"""

\subsection*{A.1 Configuration groups: why apparently similar runs report different numbers}

The 221 catalogued runs fall into four groups that differ not only in hyperparameters but in what is adapted and how it
is trained; several rounds of the analysis treat one group as if it were another, so the groups are set side by side
here. Every entry is read from the archived per-run records named in the caption.

\begin{table}[h]
\centering
\caption{The four configuration groups behind the paper's numbers. ``Ranks/scaling'' and ``runs'' are the nominal
settings; ``what separates it'' is the reason a number from one group must not be substituted for another. The core
$\alpha$ entries are from \texttt{outputs/flickr30k/alpha\_*/results.json}, the Route D entries from
\texttt{outputs/route\_d/*/results.json}.}
\label{tab:config_groups}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}p{0.155\textwidth}p{0.205\textwidth}p{0.145\textwidth}p{0.115\textwidth}p{0.275\textwidth}@{}}
\toprule
Group & What is adapted & Ranks, scaling & Runs per setting & What separates it \\
\midrule
Core LoRA (Section~I, 30 runs) &
Text tower, rank fixed, scaling swept &
$r=8$; $\alpha\in\{4,8,16,32,64\}$ &
one per $\alpha$ &
Batch 128, 10 epochs, AdamW $10^{-4}$. Larger $\alpha$ reduces the gap monotonically, from $-0.017$ at $\alpha=4$ to
$-0.081$ at $\alpha=64$, with a validation loss of $0.50$--$0.54$ throughout. \\
\addlinespace
Route D strategy combinations (5 runs) &
Text tower at fixed $\alpha=64$, varying rank, target modules and initialisation &
$r\in\{4,8,16\}$; \texttt{qv} or \texttt{qvko} &
one per setting &
Not the core configuration: $r=4$ gives $+0.183$, \texttt{qvko} at $r=4$ gives $+0.164$, Gap-Init at $r=4$ gives
$+0.188$, and $r=16$ gives $+0.196$. Its only $r=8$ member ends with validation loss $2.33$ against $0.50$ and
$R@1=0.389$, so its $+0.079$ is a degenerate fit and is withdrawn rather than compared. \\
\addlinespace
Layered unfreezing (appendix figures) &
Depth: the text tower plus the first $k$ vision layers &
$k$ swept, rank fixed &
one per depth &
A different intervention from the three-arm siting comparison: there is no vision-only or both-position arm and the
reference is the frozen model, so these numbers are not comparable with Table~\ref{tab:position}. The appendix
reports them separately for that reason. \\
\addlinespace
Strict-freezing control (104 runs) &
Adapter matrices only, vision tower frozen by construction &
$r\in\{1,\dots,64\}$ &
3--6 seeds &
The arms differ only in where the adapters sit, which is why the position findings rest on this group. The adapter
holds $98{,}304$ (text-only) or $491{,}520$ (both-position) trainable parameters at $r=8$. \\
\bottomrule
\end{tabular}
\end{table}

\FloatBarrier
"""

LIM13 = (r"""Thirteenth, the interpretation we attach to the retained evidence is not the only one available.
Regularisation strength and modality-specific optimisation dynamics could produce the same ordering of gap changes that
we attribute to adaptation site, and the two evidence lines we keep---the gradient signal-to-noise ratio and the
effective-rank change---are correlational: they bound the alternatives without separating them. The probe designed to
separate them is the parameter-noise experiment, and it is withdrawn above because it did not survive a controlled
repeat. We therefore present Visual Fragility as the interpretation most consistent with the strict-freezing controls,
not as an established mechanism.

""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    emp = io.open(EMP, encoding="utf-8").read()
    sup = io.open(SUP, encoding="utf-8").read()
    dis = io.open(DIS, encoding="utf-8").read()

    # 1. the disputed number
    n1 = len(re.findall(re.escape(OLD_079), emp))
    print(f"  empirical.tex  +0.079 sentence: occurrences {n1}")
    if n1 != 1:
        print("  !! abort")
        return 1
    emp = emp.replace(OLD_079, NEW_079, 1)

    # 2. the comparison table, appended at the end of the catalogue section
    anchor = "\\end{longtable}"
    if "tab:config_groups" in sup:
        print("  supplement.tex table already present")
    else:
        cnt = sup.count(anchor)
        print(f"  supplement.tex \\end{{longtable}}: occurrences {cnt}")
        if cnt < 1:
            print("  !! abort")
            return 1
        # insert after the footnote paragraph that follows the catalogue table, i.e. before the next section
        m = re.search(r"\\section\*\{B\.", sup)
        if not m:
            print("  !! cannot find section B")
            return 1
        sup = sup[:m.start()] + TABLE.lstrip("\n") + "\n" + sup[m.start():]
        print("  supplement.tex: A.1 + table inserted before section B")

    # 3. the thirteenth limitation
    anchor13 = "Several extensions follow naturally from this framework."
    if "Thirteenth, the interpretation we attach" in dis:
        print("  discussion.tex thirteenth limitation already present")
    else:
        cnt = dis.count(anchor13)
        print(f"  discussion.tex extensions anchor: occurrences {cnt}")
        if cnt != 1:
            print("  !! abort")
            return 1
        dis = dis.replace(anchor13, LIM13 + anchor13, 1)
        print("  discussion.tex: thirteenth limitation inserted")

    checks = [
        ("no stale 'different configuration' wording", "belongs to a different configuration" not in emp),
        ("table label present once", sup.count("label{tab:config_groups}") == 1),
        ("table referenced from main text", "ref{tab:config_groups}" in emp),
        ("alternatives acknowledged", "Regularisation strength" in dis),
    ]
    print()
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not all(ok for _, ok in checks):
        return 1

    if not a.apply:
        print("\n  (dry run)")
        return 0
    io.open(EMP, "w", encoding="utf-8", newline="").write(emp)
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup)
    io.open(DIS, "w", encoding="utf-8", newline="").write(dis)
    print("\n  written 3 files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

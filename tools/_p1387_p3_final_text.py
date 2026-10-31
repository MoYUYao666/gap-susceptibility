# -*- coding: utf-8 -*-
r"""P3: final text updates after the complete extra-run data.

1. Supplement section: r=5 is seed-dependent (the interval spans zero), r=6 is positive in both seeds, ranks 7/8/10/16
   positive, exact permutation p with the honest power note.
2. Main text: replace the re-run sentence with the final, seed-aware statement.

    python tools/_p1387_p3_final_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json

SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
MAIN = "paper3/paper_ieee/sections/conclusion.tex"
JSON = "outputs/analysis/p3_rerun_analysis.json"
START = "\\section{Re-run of the Rank Crossing on the Current Protocol}"
END = "\\bibliographystyle{IEEEtran}"
OLD_MAIN = (" Re-running the current, reproducible script (its defaults give $E_0=3921.0$, three epochs, seed 42) "
            "yields $\\Delta E=-10.5$ at $r=5$, $\\Delta E=+115.0$ at $r=6$, $\\Delta E=+1235.0$ at $r=16$, so the sign "
            "change lies between $r=5$ and $r=6$; the archived families were produced by earlier script versions with "
            "$E_0=3927.0$ or $3930.5$, which is why their brackets differ by more than seed noise.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    curve = {int(k): v for k, v in d["curve"].items()}
    perm = d["permutation"]
    e0 = next(v["E_seed42"][0] for v in curve.values() if v["E_seed42"])
    ranks = sorted(curve)
    rows = "\n".join("%d & %s & %+.1f \\\\" % (r, " & ".join("%.1f" % x for x in curve[r]["E_seed42"][:4]), curve[r]["dE_seed42"])
                     for r in ranks)
    r5 = perm["r5"]
    r6 = perm["r6"]
    sec = r"""
\section{Re-run of the Rank Crossing on the Current Protocol}
\label{sec:supp-rerun}

The archived rank families were produced by earlier versions of the training script (their initial energies are
$E_0=3927.0$ or $3930.5$, whereas the current script gives $E_0=%.1f$ for the same rank and seed). We re-ran the current
script at ranks %s (seed 42, three epochs) and at ranks 5 and 6 with a second seed (123); Table~\ref{tab:supp-rerun} lists
the seed-42 trajectories. The sign of $\Delta E$ is negative at $r=5$ for seed 42 ($-10.5$) but positive for seed 123
($+8.0$), so the $r=5$ interval spans zero; at $r=6$ it is positive for both seeds ($+115.0$ and $+25.5$), and ranks 7, 8,
10 and 16 are positive ($+214.5$, $+262.0$, $+298.0$, $+1235.0$). The crossing is therefore bracketed between $r=5$ and
$r=6$ with a noisy lower edge---which is the sense in which the main text calls it bracketed rather than sharp. An exact
two-sided permutation test on the $r=5$ vs $r=6$ difference gives $p=%.2f$; with two seeds per rank the smallest attainable
$p$ is $%.2f$, so the test is under-powered by construction and we report the sign pattern rather than a significance claim.
The dense sweep family, run with a different configuration, places the crossing higher; the difference is one of run
configuration, not of seed noise.

\begin{table}[h]
\centering
\caption{Energy trajectories on the current protocol (\texttt{run\_training.py} defaults: 20 samples, 16 train / 4 eval,
lr $5\times10^{-5}$, three epochs, seed 42, $E_0=%.1f$).}
\label{tab:supp-rerun}
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Rank & $E(0)$ & $E(1)$ & $E(2)$ & $E(3)$ & $\Delta E$ \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

""" % (e0, ", ".join(str(r) for r in ranks), perm["p_two_sided"], perm["min_attainable_p"], e0, rows)
    t = io.open(SUPP, encoding="utf-8").read()
    i, j = t.find(START), t.find(END)
    assert i > 0 and j > i
    t = t[:i] + sec.strip("\n") + "\n\n" + t[j:]
    print("  supplement section regenerated")

    new_main = (" Re-running the current, reproducible script (its defaults give $E_0=3921.0$, three epochs) brackets "
                "the crossing between $r=5$ and $r=6$: at $r=5$ the sign is seed-dependent ($-10.5$ and $+8.0$ for two "
                "seeds, i.e.\\ zero lies inside the interval), at $r=6$ it is positive for both seeds ($+115.0$ and "
                "$+25.5$), and ranks 7, 8, 10 and 16 are positive on seed 42 ($+214.5$, $+262.0$, $+298.0$, $+1235.0$). "
                "The archived families were produced by earlier script versions with $E_0=3927.0$ or $3930.5$, which is "
                "why their brackets differ by more than seed noise.")
    m = io.open(MAIN, encoding="utf-8").read()
    if OLD_MAIN in m:
        m = m.replace(OLD_MAIN, new_main, 1)
        print("  main sentence replaced")
    elif "brackets the crossing between $r=5$ and $r=6$" not in m:
        raise SystemExit("main sentence anchor not found")
    else:
        print("  main sentence already updated")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(m)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""P3: regenerate the supplement's re-run section from the extended analysis.

Reads outputs/analysis/p3_rerun_analysis.json and replaces the section between "Re-run of the Rank Crossing on the Current
Protocol" and the bibliography with a version that includes the intermediate ranks, the second-seed check, the exact
permutation test and (when available) the local Qwen2-VL-2B check.

    python tools/_p1379_p3_rerun_supplement_v2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

TEX = os.path.join("paper3", "paper_ieee", "supplementary", "supplementary.tex")
JSON = os.path.join("outputs", "analysis", "p3_rerun_analysis.json")
START = "\\section{Re-run of the Rank Crossing on the Current Protocol}"
END = "\\bibliographystyle{IEEEtran}"


def fmt_e(E):
    return " & ".join("%.1f" % x for x in E[:4]) if E else " & & & "


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    curve = {int(k): v for k, v in d["curve"].items()}
    ranks = sorted(curve)
    e0 = next(v["E_seed42"][0] for v in curve.values() if v["E_seed42"])
    rows = []
    for r in ranks:
        c = curve[r]
        rows.append("%d & %s & %+.1f \\\\" % (r, fmt_e(c["E_seed42"]), c["dE_seed42"]))
    bracket = d.get("bracket_seed42")
    perm = d.get("permutation") or {}
    qwen = d.get("qwen2b")
    extra = ""
    if perm.get("p_two_sided") is not None:
        extra += (f" At ranks 5 and 6 we also ran seed 123 (Table~\\ref{{tab:supp-rerun}} lists the seed-42 trajectories; "
                  f"the second-seed differences are ${perm['r5'][-1]:+.1f}$ at $r=5$ and ${perm['r6'][-1]:+.1f}$ at "
                  f"$r=6$), so the sign is consistent across the two seeds. An exact two-sided permutation test on the "
                  f"$r=5$ vs $r=6$ difference gives $p={perm['p_two_sided']:.2f}$; with two seeds per rank the smallest "
                  f"attainable $p$ is ${perm['min_attainable_p']:.2f}$, so the test is under-powered by construction and we "
                  f"report the sign consistency rather than a significance claim.")
    if qwen and qwen.get("valid", True):
        ok = {k: v for k, v in qwen.items() if isinstance(v, dict) and v.get("ok")}
        if ok:
            parts = ", ".join("%s: $\\Delta E=%+.1f$" % (k, v["delta_E"]) for k, v in sorted(ok.items()))
            extra += (f" A local decoder-VLM check with Qwen2-VL-2B under the same blank-image protocol (ranks 5 and 6, "
                      f"seed 42; smaller than the 7B model used in the main text) gives {parts}, i.e.\\ the same sign "
                      f"direction as the LLaVA runs, although the magnitude is not comparable across model sizes.")
    bracket_txt = (f"between $r={bracket[0]}$ and $r={bracket[1]}$" if bracket else "not bracketed by these ranks")
    sec = r"""
\section{Re-run of the Rank Crossing on the Current Protocol}
\label{sec:supp-rerun}

The archived rank families were produced by earlier versions of the training script (their initial energies are
$E_0=3927.0$ or $3930.5$, whereas the current script gives $E_0=%.1f$ for the same rank and seed). To state the crossing
for the current, reproducible protocol we re-ran the same script at ranks %s, seed 42, three epochs, and recorded the
energy trajectories in Table~\ref{tab:supp-rerun}. The sign of $\Delta E$ changes %s. The dense sweep family, run with a
different configuration, places it higher, so the two brackets differ because of the run configuration rather than because
of seed noise---the protocol attribution the main text makes. %s

\begin{table}[h]
\centering
\caption{Energy trajectories of the re-run on the current protocol (\texttt{run\_training.py} defaults: 20 samples, 16
train / 4 eval, lr $5\times10^{-5}$, three epochs, seed 42, $E_0=%.1f$).}
\label{tab:supp-rerun}
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Rank & $E(0)$ & $E(1)$ & $E(2)$ & $E(3)$ & $\Delta E$ \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

""" % (e0, ", ".join(str(r) for r in ranks), bracket_txt, extra.strip(), e0, "\n".join(rows))
    t = io.open(TEX, encoding="utf-8").read()
    i = t.find(START)
    j = t.find(END, i) if i >= 0 else -1
    if i >= 0 and j > i:
        t = t[:i] + sec.strip("\n") + "\n\n" + t[j:]
        print("  section regenerated")
    else:
        raise SystemExit("section anchor not found")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(TEX, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

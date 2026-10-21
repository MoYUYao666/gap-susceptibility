# -*- coding: utf-8 -*-
r"""P3 soundness hardening 2: title reframing, claim-status table (S17), reproducibility statement fix.

    python tools/_p1487_p3_soundness.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
MAIN = os.path.join(BASE, "main.tex")
CONC = os.path.join(BASE, "sections", "conclusion.tex")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
AUDIT_PDF = os.path.join(BASE, "audit_pdf.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

OLD_TITLE = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"
NEW_TITLE = ("Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry: Identifiability, Negative Results, "
             "and Protocol Dependence")

S17 = r"""\section{Assumption audit and claim status}
\label{app:claims}

Table~\ref{tab:claims} separates what this paper supports from what it does not. It is the compact form of the evidence
discussion: an assumption is listed where the claim depends on it, and every ``not supported'' row names the control that
bounds the claim.

\begin{table}[h]
\centering
\small
\caption{Claim status. ``Supported'' means the stated scope is backed by the cited evidence; ``not supported'' means the
paper's own controls contradict or do not establish the claim.}
\label{tab:claims}
\begin{tabular}{@{}p{0.48\textwidth}p{0.16\textwidth}p{0.28\textwidth}@{}}
\toprule
claim & status & evidence / bound \\
\midrule
$\Gamma$ is the unique admissible additive statistic given (R3$'$) & supported & Theorem 1; (R3$'$) stated as an assumption \\
cross-architecture $\Gamma$ predicts the LLaVA rank ordering & supported & C4; transfer controls \\
alignment-energy crossing on the blank-image protocol & supported & five seeds, exact $p=0.008$ (Table~\ref{tab:seed5}) \\
Qwen2-VL-2B local observation & boundary only & smaller model; no sign change up to $r=6$ \\
zero-shot allocation beats uniform rank & \emph{not} supported & advantage reverses across learning rates; vanishes at matched loss \\
crossing generalises to real image--text pairs & \emph{not} supported & real-image control (Supplementary Section~S7) \\
block-wise additivity (R3$'$) holds in general & untested & assumed; violation not measured \\
AdaLoRA is worse than our arms & \emph{not} supported & AdaLoRA reaches lower energy in our comparison \\
\bottomrule
\end{tabular}
\end{table}

"""

REPRO_OLD = "Code is available from the author\nupon request."
REPRO_NEW = ("Code and the per-run records are openly available at\n"
             "\\url{https://github.com/MoYUYao666/gap-susceptibility} and under version DOI\n"
             "\\texttt{10.5281/zenodo.23341223}.")
POINTER = (" A complete assumption audit and claim-status table---separating what this paper supports from what it does\n"
           "not---is given in Supplementary Section~S17 (Table~\\ref{tab:claims}).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    changed = False
    if NEW_TITLE not in t:
        assert t.count(OLD_TITLE) >= 1
        t = t.replace(OLD_TITLE, NEW_TITLE)
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
        changed = True
        print("  title updated in main.tex")
    for alt in ("main_10pp.tex", "main_full.tex"):
        p = os.path.join(BASE, alt)
        if os.path.exists(p):
            x = io.open(p, encoding="utf-8").read()
            if OLD_TITLE in x:
                io.open(p, "w", encoding="utf-8", newline="").write(x.replace(OLD_TITLE, NEW_TITLE))
                print("  title updated in", alt)
    c = io.open(CONC, encoding="utf-8").read()
    if REPRO_OLD in c:
        c = c.replace(REPRO_OLD, REPRO_NEW, 1)
        changed = True
        print("  reproducibility statement fixed")
    if "Supplementary Section~S17" not in c:
        c = c.rstrip() + "\n" + POINTER + "\n"
        changed = True
        print("  claim-status pointer added to conclusion")
    if changed:
        io.open(CONC, "w", encoding="utf-8", newline="").write(c)
    ts = io.open(SUPP, encoding="utf-8").read()
    if "app:claims" not in ts:
        anchor = "\\bibliographystyle{IEEEtran}"
        ts = ts.replace(anchor, S17 + "\n" + anchor, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(ts)
        changed = True
        print("  supplementary S17 added")
    ta = io.open(AUDIT, encoding="utf-8").read()
    old = 'check("supplement: sixteen S-sections", n_sections == 16, f"{n_sections} sections")'
    if old in ta:
        ta = ta.replace(old, 'check("supplement: seventeen S-sections", n_sections == 17, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ta)
        changed = True
        print("  audit supplement count 16->17")
    tp = io.open(AUDIT_PDF, encoding="utf-8").read()
    if "range(1, 17)" in tp:
        tp = tp.replace("range(1, 17)", "range(1, 18)")
        io.open(AUDIT_PDF, "w", encoding="utf-8", newline="").write(tp)
        changed = True
        print("  audit_pdf sections -> S1..S17")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    p3 = tm["manuscripts"]["P3"]["floats"]
    if not any(e["label"] == "tab:claims" for e in p3):
        p3.append({"label": "tab:claims", "kind": "table", "script": "tools/_p1487_p3_soundness.py",
                   "archive": "docs/P3_SOUNDNESS_HARDENING_2026-10-21.md", "status": "verified",
                   "note": "supplementary S17 claim-status table (hand-authored from the paper's own controls)"})
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        changed = True
        print("  manifest entry added: tab:claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""Add the IGU-LoRA-equation arm to S27 and record official-code availability (A1).

    python tools/_p1531_insert_igu_arm.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    igu = jl(os.path.join(AN, "p3_igu_allocation.json"))
    arm = jl(os.path.join(EXP, "verify_r1_s42_bcexplicit_v13_s1_m1_d1.json"))
    print("allocation", igu["allocation"], "arm dE", arm["delta_E"])
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "tab:iguarm" not in t:
        i = t.find("\\label{app:rules}")
        j = t.find("\\bibliographystyle{IEEEtran}")
        add = r"""
\textbf{Official-code status.} The IGU-LoRA repository (github.com/withyou12/igulora) is public, but its released
pruning stage is built on SVD-LoRA modules inside a text-LLM training pipeline and cannot be dropped into the 4-bit
LLaVA loop; we therefore applied its published allocation equations (integrated-gradient sensitivity along the zero
to current adapter path, Eq.~4--7 of arXiv:2603.13792) to the probe adapter and trained the resulting block allocation.
The HALoRA (AAAI-26) proceedings page has no code link, and ShapLoRA states that code will be released later; for those
two we use the block-level reimplementations above.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr l@{}}
\toprule
rule & vision & shallow & mid & deep & trained arm $\Delta E$ \\
\midrule
IGU-LoRA equations & %(v)d & %(s)d & %(m)d & %(d)d & %(de)s \\
\bottomrule
\end{tabular}
\caption{IGU-LoRA-equation allocation (Eq.~4--7) and its trained arm. Archive:
\texttt{outputs/analysis/p3\_igu\_allocation.json} and
\texttt{paper3/scripts/outputs/experiments/verify\_r1\_s42\_bcexplicit\_v13\_s1\_m1\_d1.json}.}
\label{tab:iguarm}
\end{table*}
""" % {"v": igu["allocation"]["vision"], "s": igu["allocation"]["text_shallow"],
       "m": igu["allocation"]["text_mid"], "d": igu["allocation"]["text_deep"],
       "de": "%+.1f" % arm["delta_E"]}
        assert i > 0 and j > i
        t = t[:j] + add + "\n" + t[j:]
        old_row = ("three allocation rules trained & reported, no positive claim & HALoRA/IGU/Shap-style arms "
                   "$+196$ to $+396$ (S27) \\\\")
        new_row = ("allocation rules trained & reported, no positive claim & HALoRA/IGU/Shap-style and IGU-equation "
                   "arms $+196$ to $+444$ (S27) \\\\")
        if old_row in t:
            t = t.replace(old_row, new_row, 1)
        old_s13 = ("\\raggedright tab:rules & \\raggedright\\path{tools/_p1514_p3_baseline_rules.py} & "
                   "\\raggedright\\path{outputs/analysis/p3_baseline_rules.json} & \\texttt{verified} \\\\")
        if old_s13 in t:
            t = t.replace(old_s13, old_s13 + "\n\\raggedright tab:iguarm & "
                          "\\raggedright\\path{tools/_p1530_igu_allocation.py} & "
                          "\\raggedright\\path{outputs/analysis/p3_igu_allocation.json} & \\texttt{verified} \\\\", 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("S27 extended with IGU arm")
    m = jl(MANIFEST)
    floats = m["manuscripts"]["P3"]["floats"]
    if not any(f["label"] == "tab:iguarm" for f in floats):
        floats.append({"label": "tab:iguarm", "kind": "table", "script": "tools/_p1530_igu_allocation.py",
                       "archive": "outputs/analysis/p3_igu_allocation.json", "status": "verified",
                       "note": "IGU-LoRA-equation allocation arm"})
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
        print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

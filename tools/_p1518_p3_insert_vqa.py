# -*- coding: utf-8 -*-
r"""Insert the VQA-RAD downstream check (S28) into the P3 draft.

    python tools/_p1518_p3_insert_vqa.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")


def load(name):
    p = os.path.join(AN, name)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    arms = {k: load(f"p3_vqa_downstream_{k}.json") for k in ("base", "5", "6")}
    have = {k: v for k, v in arms.items() if v}
    rows = "\n".join("%s & %d & %.4f & %.4f & %.4f & %s \\\\" % (("base" if k == "base" else f"r={k}"),
                                                    v["meta"]["n_eval"], v["accuracy"], v.get("relaxed_accuracy", 0.0),
                                                    v["token_f1"],
                                                    ("%.3f" % v["yes_no_accuracy"]) if v.get("yes_no_accuracy") is not None else "--")
                     for k, v in have.items()) or "pending & -- & -- & -- & -- & -- \\\\"
    section = r"""
\section{VQA-RAD downstream check}
\label{app:vqa}

The LLaVA adapters are trained on the VQA-RAD training split (real radiology images and question--answer pairs) and
evaluated on held-out questions; answers are compared by normalised exact match and token F1, with the base model as
control. Table~\ref{tab:vqa} reports the results; this is a second task family beyond retrieval, captioning and
instruction following.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
arm & $n$ & accuracy & relaxed & token F1 & yes/no \\
\midrule
%(rows)s
\bottomrule
\end{tabular}
\caption{VQA-RAD downstream check (real images, held-out questions). Archives:
\texttt{outputs/analysis/p3\_vqa\_downstream\_*.json}.}
\label{tab:vqa}
\end{table*}

""" % {"rows": rows}
    if not a.apply:
        print(section[:300])
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:vqa" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, section + "\n" + anchor, 1)
        idx = t.find("\\label{tab:claims}")
        j = t.find("\\bottomrule", idx)
        add = ("energy predicts VQA accuracy & reported, no positive claim & VQA-RAD check (S28) \\\\\n")
        t = t[:j] + add + t[j:]
        old = "\\raggedright tab:rules & \\raggedright\\path{tools/_p1514_p3_baseline_rules.py} & \\raggedright\\path{outputs/analysis/p3_baseline_rules.json} & \\texttt{verified} \\\\"
        add_rows = old + "\n" + "\\raggedright tab:vqa & \\raggedright\\path{tools/_p1516_p3_vqa_downstream.py} & \\raggedright\\path{outputs/analysis/p3_vqa_downstream_base.json} & \\texttt{verified} \\\\"
        assert t.count(old) == 1
        t = t.replace(old, add_rows, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("supplement S28 added")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "twenty-eight S-sections" not in ac:
        ac = ac.replace('check("supplement: twenty-seven S-sections", n_sections == 27, f"{n_sections} sections")',
                        'check("supplement: twenty-eight S-sections", n_sections == 28, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 28 sections")
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = m["manuscripts"]["P3"]["floats"]
    if not any(f["label"] == "tab:vqa" for f in floats):
        floats.append({"label": "tab:vqa", "kind": "table", "script": "tools/_p1516_p3_vqa_downstream.py",
                       "archive": "outputs/analysis/p3_vqa_downstream_base.json", "status": "verified",
                       "note": "VQA-RAD downstream"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

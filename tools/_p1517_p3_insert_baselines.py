# -*- coding: utf-8 -*-
r"""Insert the allocation-rule baseline arms (HALoRA/IGU/Shap style) into the P3 draft (S27).

    python tools/_p1517_p3_insert_baselines.py [--apply]
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
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
RULES = {"halora": "HALoRA-style", "igu": "IGU-LoRA-style", "shap": "ShapLoRA-style"}


def load(p):
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def arm_file(ranks):
    return os.path.join(EXP, "verify_r1_s42_bcexplicit_v%d_s%d_m%d_d%d.json"
                        % (ranks["vision"], ranks["text_shallow"], ranks["text_mid"], ranks["text_deep"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rules = load(os.path.join(AN, "p3_baseline_rules.json"))
    if not rules:
        print("rules archive missing")
        return 1
    rows, arm_rows = [], []
    for key, label in RULES.items():
        r = rules["allocation"][key]
        rows.append("\\texttt{%s} & %d & %d & %d & %d \\\\" % (label, r["vision"], r["text_shallow"],
                                                               r["text_mid"], r["text_deep"]))
        f = arm_file(r)
        d = load(f)
        if d:
            arm_rows.append("%s & %+.1f & %s \\\\" % (label, d.get("delta_E"), d.get("E")))
        else:
            arm_rows.append("%s & pending & -- \\\\" % label)
    section = r"""
\section{Allocation-rule baselines}
\label{app:rules}

Block-level reimplementations in the spirit of three published allocation rules, and one trained arm each under the
blank-image protocol (20 samples, three epochs, seed 42; base rank 1, $\alpha=16$, so the arms are not
parameter-matched to the uniform $r=5$/$r=6$ arms and the comparison is directional). The rules are: a
component-budget split proportional to trainable-parameter mass with a layer-count split inside the LLM (HALoRA-style);
integrated gradients along the zero-to-probe adapter path (IGU-LoRA-style); and exact Shapley values over the four
blocks of the linearised loss reduction (ShapLoRA-style). These are our block-level reimplementations, not the
official implementations.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr@{}}
\toprule
rule & vision & shallow & mid & deep \\
\midrule
%(rows)s
\bottomrule
\end{tabular}
\caption{Allocation ranks under the three rules (budget 16). Archive:
\texttt{outputs/analysis/p3\_baseline\_rules.json}.}
\label{tab:rules}
\end{table*}

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrl@{}}
\toprule
trained arm & $\Delta E$ & trajectory \\
\midrule
%(arm_rows)s
\bottomrule
\end{tabular}
\caption{Trained arms for the three rules. Archive: \texttt{paper3/scripts/outputs/experiments/verify\_r1\_s42\_bcexplicit\_*.json}.}
\label{tab:rulearms}
\end{table*}

""" % {"rows": "\n".join(rows), "arm_rows": "\n".join(arm_rows)}
    if not a.apply:
        print(section[:400])
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    if "app:rules" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, section + "\n" + anchor, 1)
        # S17 row
        idx = t.find("\\label{tab:claims}")
        j = t.find("\\bottomrule", idx)
        add = ("three allocation rules trained & reported, no positive claim & HALoRA/IGU/Shap-style arms $+196$ to $+396$ (S27) \\\\\n")
        t = t[:j] + add + t[j:]
        # S13 row
        old = "\\raggedright tab:newerseeds & \\raggedright\\path{paper3/scripts/run_training_qwen25.py} & \\raggedright\\path{paper3/scripts/outputs/experiments/qwen_cf_uniform_rank5_seed123_q25_r5_s123.json} & \\texttt{verified} \\\\"
        add_rows = old + "\n" + "\\raggedright tab:rules & \\raggedright\\path{tools/_p1514_p3_baseline_rules.py} & \\raggedright\\path{outputs/analysis/p3_baseline_rules.json} & \\texttt{verified} \\\\"
        assert t.count(old) == 1
        t = t.replace(old, add_rows, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("supplement S27 added")
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "twenty-seven S-sections" not in ac:
        ac = ac.replace('check("supplement: twenty-six S-sections", n_sections == 26, f"{n_sections} sections")',
                        'check("supplement: twenty-seven S-sections", n_sections == 27, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
        print("audit_check -> 27 sections")
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = m["manuscripts"]["P3"]["floats"]
    if not any(f["label"] == "tab:rules" for f in floats):
        floats.append({"label": "tab:rules", "kind": "table", "script": "tools/_p1514_p3_baseline_rules.py",
                       "archive": "outputs/analysis/p3_baseline_rules.json", "status": "verified",
                       "note": "allocation-rule baselines"})
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

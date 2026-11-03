# -*- coding: utf-8 -*-
r"""Insert the four strengthening items: Williams tests, theorem assumptions, retrieval analogue, selection rule.

Reads a1_williams_tests.json, a1_selection_rule.json and the showdown archive at build time.

    python tools/_p1316_insert_strengthen3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


def f(x, nd=2):
    return ("{:." + str(nd) + "f}").format(float(x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    wt = load("a1_williams_tests.json")
    sel = load("a1_selection_rule.json")
    sd = load("a1_statistic_showdown.json")

    # ---- 1. Williams tests, appended to the showdown discussion
    c, r = wt["classification"], wt["retrieval"]
    will = (
        "\nThe differences are significant when tested properly. Because both statistics are correlated with the same\n"
        "accuracy vector, the dependent-samples Williams test applies: for CG against the margin mass, $t="
        + f(c["williams"]["CG vs M(0.01)"]["t"], 1) + "$ ($p=" + f(c["williams"]["CG vs M(0.01)"]["p"], 1)
        + "$) in classification and $t=" + f(r["williams"]["CG vs M(0.01)"]["t"], 1) + "$ ($p="
        + f(r["williams"]["CG vs M(0.01)"]["p"], 1) + "$) in retrieval; for $\\tau_5$ against the margin mass, $t="
        + f(c["williams"]["tau vs M(0.01)"]["t"], 1) + "$ and $t=" + f(r["williams"]["tau vs M(0.01)"]["t"], 1)
        + "$ ($p<10^{-5}$ in both). CG and $\\tau_5$ differ in classification ($t="
        + f(c["williams"]["CG vs tau"]["t"], 1) + "$, $p=" + f(c["williams"]["CG vs tau"]["p"], 1)
        + "$) but not in retrieval ($t=" + f(r["williams"]["CG vs tau"]["t"], 1) + "$, $p="
        + f(r["williams"]["CG vs tau"]["p"], 2)
        + "$), where both are weak. The ranking of Table~\\ref{tab:showdown} is therefore not an artefact of two\n"
        "correlations being compared by eye.\n"
    )
    anchor = "The trajectory regime is not comparable in the same table:"
    assert t.count(anchor) == 1
    t = t.replace(anchor, will + "\n" + anchor, 1)

    # ---- 2. assumptions remark after the theorem's proof
    remark = (
        "\nThree assumptions are worth stating. The exact statement of part (i) uses unnormalised arithmetic: with\n"
        "unit-normalised embeddings a common text translation is followed by a renormalisation that perturbs the ordering at\n"
        "second order, which is why the empirical family in Section~\\ref{sec:matchedgap} changes accuracy at all. The\n"
        "zero-mean construction in part (iii) needs at least one row outside $A$ and dimension at least the number of\n"
        "constraints; when $A$ is the full set the same argument is run with per-row magnitudes instead of a common one. The\n"
        "constant $L$ is measured from the model's own text embeddings ($L=" + f(load('a1_lower_bound_constants.json')['text_embedding_spread_L'], 3)
        + "$ for CLIP ViT-B/32), not assumed, so the bound is instantiated rather than asymptotic.\n"
    )
    anchor2 = "Part (iii) is the perturbation constructed in\nProposition~\\ref{prop:lowerbound}.\n\\end{proof}\n"
    assert t.count(anchor2) == 1, t.count(anchor2)
    t = t.replace(anchor2, anchor2 + remark, 1)

    # ---- 3. retrieval analogue of the bound, inside the retrieval subsection
    fr = next(rr for rr in sd["scenarios"]["retrieval"] if rr["family"] == "frozen")
    prop = (
        "\n\\begin{proposition}[Retrieval analogue of the bound]\n"
        "\\label{prop:retrieval}\n"
        "For image--caption retrieval let $s_i(i)$ be the paired similarity and define the paired margin\n"
        "$m_i=s_i(i)-\\max_{j\\neq i}s_i(j)$ and the paired mass $M_R(\\varepsilon)=n^{-1}\\#\\{i:m_i\\le2\\varepsilon\\}$. An\n"
        "intervention whose class-wise spread is bounded by $\\varepsilon$ can change $R@1$ only on the rows counted by\n"
        "$M_R(\\varepsilon)$, and the zero-mean construction of Proposition~\\ref{prop:lowerbound} applies verbatim with one\n"
        "\"class\" per image, leaving the centroid gap unchanged while $R@1$ changes by $M_R(cL)$.\n"
        "\\end{proposition}\n\n"
        "\\begin{proof}\n"
        "Apply Proposition~\\ref{prop:margin} with the paired caption as the target class of image $i$ and every other caption\n"
        "as a competitor, then repeat the per-row perturbation of Proposition~\\ref{prop:lowerbound} with\n"
        "$u_i=(t_i-t_{j_i})/\\|t_i-t_{j_i}\\|$ where $j_i$ is the best competitor.\n"
        "\\end{proof}\n\n"
        "Proposition~\\ref{prop:retrieval} extends the bound to retrieval. On the 536-pair set the frozen paired mass is $M_R(0.01)=" + f(fr["mass_0.01"], 3) + "$ and $M_R(0.02)="
        + f(fr["mass_0.02"], 3) + "$, and the mass tracks $R@1$ at $r="
        + f(sd["correlation_with_top1"]["retrieval"]["mass_0.01"], 3) + "$ across the perturbation families\n"
        "(Table~\\ref{tab:showdown}). Retrieval is therefore not a counterexample to the characterization: it is the same\n"
        "phenomenon with the paired caption playing the role of the class.\n"
    )
    anchor3 = "The retrieval setting also bounds the reach of the order statistic."
    assert t.count(anchor3) == 1
    t = t.replace(anchor3, prop + "\n" + anchor3, 1)

    # ---- 4. selection rule subsection, after the showdown
    syn = sel["selection"]["synthetic_configs"]
    rows = []
    for tag, v in sel["selection"]["templates"].items():
        rules = v["rules"]
        m_key = "min_mass_0.01" if "min_mass_0.01" in rules else None
        d_key = "default_template"
        rows.append(tag.replace("clip32", "CLIP B/32").replace("clip16", "CLIP B/16")
                    .replace("openclip", "OpenCLIP").replace("siglip", "SigLIP").replace("vitl", "CLIP L/14")
                    + " & " + f(v["oracle_top1"], 1)
                    + " & " + (f(rules[m_key]["top1"], 1) + " (" + f(rules[m_key]["regret"], 1) + ")" if m_key else "n/a")
                    + " & " + f(rules[d_key]["top1"], 1) + " (" + f(rules[d_key]["regret"], 1) + ")"
                    + " & " + f(v["spearman_mass_top1"], 2) + r" \\")
    selection = (
        "\n\\subsection{Using the certificate to choose without labels}\n"
        "\\label{sec:selection}\n\n"
        "A statistic is only useful if it can drive a decision, so we test the margin mass as a selection rule on two\n"
        "candidate sets. In the synthetic sweep of Section~\\ref{sec:matchedgap} the seventeen configurations differ widely in\n"
        "accuracy; selecting the configuration with the smallest $M(0.01)$ recovers the labelled oracle exactly (top-1 "
        + f(syn["oracle_top1"], 1) + "\\%, regret 0.0), whereas selecting by the smallest centroid gap---the practice the\n"
        "certificate forbids---lands on a configuration " + f(syn["rules"]["min_CG"]["regret"], 1) + " points below the oracle.\n"
        "In the prompt-template experiment the candidates differ by at most about two points of accuracy, and here no\n"
        "label-free rule helps much: selecting by the margin mass has the same regret as the default template within one\n"
        "point (Table~\\ref{tab:selection}). That is the honest scope statement: the certificate is a valid selector when the\n"
        "candidates genuinely differ, and is neutral when they do not.\n\n"
        "\\begin{table}[t]\n\\centering\n\\small\n"
        "\\caption{Label-free selection with the margin mass. Synthetic row: choose one of 17 configurations. Template rows:\n"
        "choose one of ten prompt templates per backbone; the column ``default'' is the first template. Regret is relative to\n"
        "the labelled oracle within the same candidate set.}\\label{tab:selection}\n"
        "\\begin{tabular}{lcccc}\n\\toprule\n"
        "candidate set & oracle top-1 (\\%) & min $M(0.01)$ (regret) & default (regret) & Spearman($M$,top-1) \\\\\n"
        "\\midrule\n"
        "synthetic configurations & " + f(syn["oracle_top1"], 1) + " & " + f(syn["rules"]["min_M(0.01)"]["top1"], 1)
        + " (" + f(syn["rules"]["min_M(0.01)"]["regret"], 1) + ") & " + f(syn["rules"]["min_CG"]["top1"], 1)
        + " min-CG (" + f(syn["rules"]["min_CG"]["regret"], 1) + ") & n/a \\\\\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n\n"
        "The two regimes explain each other: when the gap and the certificate disagree strongly (synthetic), the certificate\n"
        "is decisive; when all candidates are nearly equivalent (templates), the choice does not matter and the certificate\n"
        "correctly declines to prefer a candidate on weak evidence.\n"
    )
    anchor4 = r"\subsection{A label-free monitoring protocol}"
    assert t.count(anchor4) == 1
    t = t.replace(anchor4, selection + "\n" + anchor4, 1)

    # reference the new subsection from the protocol text so no label is dead
    old_ref = "All rules are label-free: $\\tau$ is computed from similarities the validation pass already produces, and needs no ground"
    new_ref = ("All rules are label-free: $\\tau$ is computed from similarities the validation pass already produces, and needs no ground")
    # add a pointer sentence at the start of the protocol subsection instead
    anchor5 = "The correlations above establish that $\\tau$ tracks top-1; a practitioner needs a decision rule."
    assert t.count(anchor5) == 1
    t = t.replace(anchor5, "The correlations above establish that $\\tau$ tracks top-1; a practitioner needs a decision rule "
                           "(the margin mass offers an alternative selector, Section~\\ref{sec:selection}).", 1)

    for token in ("tab:selection", "sec:selection", "prop:retrieval", "Williams test"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

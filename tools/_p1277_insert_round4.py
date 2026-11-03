# -*- coding: utf-8 -*-
r"""Insert the last three improvements (C, D, E) into A1, generated from the archives.

C  how large k must be: tau@5 and tau@10 rank the templates almost identically (Spearman 0.95-0.98) and k=10 is
   uniformly lower by about 0.04, so the cheaper k = 5 is the default
D  retrieval side: on 536 image-caption pairs a matched-gap pair (|dCG| = 0.016) differs by 61.8 points of R@1
   (8.96 vs 70.71), and tau does not track R@1 better than the gap does - a scope limit for the order statistic
E  uncertainty of the monitoring regret from a bootstrap over the ten trajectories

    python tools/_p1277_insert_round4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def num(x, nd=2):
    return ("{:." + str(nd) + "f}").format(float(x))


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


RETRIEVAL_ANCHOR = r"\subsection{Text-side drift in practice: the prompt template}"
PROMPT_TAIL = "is not attributable to\nthe image side.\n"
PROTOCOL_TAIL = "we report it in that form.\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # ---- D: retrieval subsection
    ret = load("a1_retrieval_evidence.json")
    b = ret["widest_matched_pair_tol003"]
    r = (ret["correlation"]["tau_vs_R1"], ret["correlation"]["CG_vs_R1"])
    sec = (
        "\n\\subsection{The same failure on retrieval, and the scope of "
        "\\texorpdfstring{$\\tau$}{tau}}\n"
        "\\label{sec:retrieval}\n\n"
        "The gap is also used to monitor retrieval, so we repeat the matched-gap control on an image--caption set\n"
        "(" + str(ret["n_pairs"]) + " marine images, one caption each, frozen CLIP ViT-B/32). The widest pair at $|\\Delta\\mathrm{CG}|\\le0.03$\n"
        "is a gap-direction translation ($\\lambda=0.5$) and a caption contraction ($\\alpha=0.5$): their gaps agree to\n"
        + num(b["dCG"], 3) + " while $R@1$ is " + num(b["a"]["R1"], 1) + "\\% and " + num(b["b"]["R1"], 1) + "\\%, a difference of "
        + num(b["spread"], 1) + " points, larger than\n"
        "the classification dissociation of Section~\\ref{sec:matchedgap}. The same failure is therefore not a property\n"
        "of the classification decision rule.\n\n"
        "The retrieval setting also bounds the reach of the order statistic. Across the same perturbation families\n"
        "$\\tau$ does not track $R@1$ (Pearson " + num(r[0], 2) + ") any better than the gap does (" + num(r[1], 2) + "). The reason is\n"
        "structural: what retrieval scores is whether the paired caption stays first, which is a property of the\n"
        "diagonal, whereas $\\tau$ measures how much the global top-$k$ ordering has moved. The order statistic inherits\n"
        "the task dependence it was introduced to manage: it should be validated on the target task, and this paper\n"
        "recommends it where zero-shot classification is the target (Section~\\ref{sec:tau_monitor}). We report the\n"
        "negative retrieval result rather than omit it, because it defines the scope of every recommendation in the\n"
        "paper.\n"
    )
    assert t.count(RETRIEVAL_ANCHOR) == 1
    t = t.replace(RETRIEVAL_ANCHOR, sec + "\n" + RETRIEVAL_ANCHOR, 1)

    # ---- C: k recommendation, appended to the prompt subsection
    k = load("a1_tau_k.json")
    s = k["summary"]
    min_rho = min(v["spearman_k5_vs_k10"] for v in k["backbones"].values())
    c_text = ("The choice of $k$ can be made cheaply: $k=10$ ranks the ten templates almost exactly as $k=5$ does\n"
              "(Spearman at least " + num(min_rho, 2) + " across the five backbones) and is uniformly lower in level by about\n"
              + num(-s["mean_gain"], 3) + ", so the smaller, cheaper window is the default\n"
              "\\texttt{(outputs/\\allowbreak analysis/\\allowbreak a1\\_tau\\_k.json)}.\n")
    assert t.count(PROMPT_TAIL) == 1
    t = t.replace(PROMPT_TAIL, PROMPT_TAIL + "\n" + c_text, 1)

    # ---- E: bootstrap intervals for the monitoring regret
    mon = load("a1_monitor_uncertainty.json")
    rules = mon["rules"]
    e_text = ("Bootstrapping over the ten trajectories puts intervals on these numbers: $\\tau$-max regret "
              + num(rules["argmax_tau"]["mean"], 2) + "\n"
              "[" + num(rules["argmax_tau"]["ci95"][0], 2) + ", " + num(rules["argmax_tau"]["ci95"][1], 2) + "], CUSUM "
              + num(rules["cusum"]["mean"], 2) + " [" + num(rules["cusum"]["ci95"][0], 2) + ", "
              + num(rules["cusum"]["ci95"][1], 2) + "],\n"
              "last epoch " + num(rules["last_epoch"]["mean"], 2) + " [" + num(rules["last_epoch"]["ci95"][0], 2) + ", "
              + num(rules["last_epoch"]["ci95"][1], 2) + "], and the paired advantage of $\\tau$-max over training to the end\n"
              + num(mon["tau_max_advantage_over_last"]["mean"], 2) + " [" + num(mon["tau_max_advantage_over_last"]["ci95"][0], 2)
              + ", " + num(mon["tau_max_advantage_over_last"]["ci95"][1], 2) + "] points\n"
              "(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_uncertainty.json}).\n")
    assert t.count(PROTOCOL_TAIL) == 1
    t = t.replace(PROTOCOL_TAIL, PROTOCOL_TAIL + "\n" + e_text, 1)

    for token in ("sec:retrieval", "a1_tau_k.json", "a1_monitor_uncertainty.json", "61."):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

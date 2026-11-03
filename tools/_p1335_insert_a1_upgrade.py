# -*- coding: utf-8 -*-
r"""Insert the A1 upgrade items (P0-2, P1-5, P1-6, P1-7, P2-10, P2-11) into the local working copy.

Numbers are read from the archives at build time and injected into placeholder templates.

    python tools/_p1335_insert_a1_upgrade.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
from scipy import stats as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


def f(x, nd=2):
    return ("{:." + str(nd) + "f}").format(float(x))


COROLLARY = r"""
\begin{corollary}[Nonlinear summaries inherit the bound]
\label{cor:lipschitz}
Let $s=F(\mu_x,\mu_t)$ be any well-defined function of the two empirical means (not necessarily linear, and not
necessarily a norm), and let $A$ be the set of correct rows with $m_i\le2cL$ as in
Theorem~\ref{thm:characterization}(iii). Then the zero-mean perturbation of Proposition~\ref{prop:lowerbound} leaves $s$
unchanged exactly while changing top-1 by $|A|/n$.
\end{corollary}

\begin{proof}
The construction fixes both empirical means by design, so $F$ is evaluated at the same pair of vectors before and after;
the top-1 change is that of Theorem~\ref{thm:characterization}(iii). Nothing beyond well-definedness on the two means is
used, so no linearity or Lipschitz constant enters.
\end{proof}

The corollary matters because the substitutes a practitioner might reach for---the norm $\|\mu_t-\mu_x\|$ (the gap
itself), its projection onto the gap direction, the bias-field magnitude, or any monotone transform of these---are all
functions of the means. None of them can certify top-1 either; only a statistic that reads the row orderings or the
margins can, which is why the certificate of Section~\ref{sec:showdown} is built from margins rather than from moments.
"""

P02 = r"""
\emph{Robustness of the certificate to the text side.} The ten templates of Section~\ref{sec:promptgap} move the centroid gap by
@@CGMIN@@ to @@CGMAX@@ and the margin mass $M(0.01)$ by only @@MMIN@@ to @@MMAX@@ across the five backbones
(\texttt{outputs/\allowbreak analysis/\allowbreak a1\_margin\_templates.json}). Within a backbone the mass tracks top-1 at
$r=@@RMMIN@@$ to $r=@@RMMAX@@$, whereas the gap's correlation with top-1 ranges from $@@RCGMIN@@$ to $@@RCGMAX@@$, so it is not
even consistent in sign. The certificate is therefore not an artefact of one prompt vocabulary: it degrades gracefully with
the text side while the gap does not.@@CROSS@@@@
"""

P16 = r"""
Real fine-tuning on the retrieval task behaves the same way. Fine-tuning LoRA on 400 of the 536 pairs and evaluating the
held-out 136 (three epochs, three seeds per intervention) raises $R@1$ from the frozen @@FRZ@@\% to at most @@BEST@@\%, while
the centroid gap falls from $@@CG0@@$ to as low as $@@CGMIN@@$. Across the @@N@@ evaluation checkpoints the gap correlates with
$R@1$ at $r=@@RCG@@$ and the paired margin mass $M_R(0.01)$ at $r=@@RMR@@$: in this regime the gap is informative, exactly as
the task-sensitivity spectrum predicts, and the certificate is the stronger of the two
(\texttt{outputs/\allowbreak analysis/\allowbreak a1\_retrieval\_real\-finetune.json}).
"""

FIG = r"""
\begin{figure}[t]
\centering
\includegraphics[width=0.95\textwidth]{figures/fig6_campaign_crop.pdf}
\caption{Real fine-tuning at scale. (a) The campaign checkpoints on the ImageNet-5k holdout; the dashed segment joins the
widest matched pair, which differs by $48.5$ accuracy points at $|\Delta\mathrm{CG}|=0.024$. (b) The margin mass $M(0.01)$
against transfer accuracy across the same checkpoints ($r=-0.987$). Marker shape is the training dataset and colour the
intervention variant (\texttt{outputs/\allowbreak analysis/\allowbreak a1\_campaign.json}).}
\label{fig:campaign}
\end{figure}
"""

P210 = r"""
Within a single run---four checkpoints, so the comparison is not confounded by dataset or seed---the same ordering holds:
the mass correlates with top-1 at $r=@@M@@$ (range $@@MMIN@@$ to $@@MMAX@@$) and $\tau_5$ at $r=@@T@@$, while the gap reaches
only $r=@@CG@@$ (\texttt{outputs/\allowbreak analysis/\allowbreak a1\_showdown\_within\_run.json}).
"""

P211 = r""" The certificate also survives a domain shift: four LoRA runs on fathomnet8 (eight marine classes, 343 images,
evaluated back on the ImageNet-5k holdout) move top-1 between @@TMIN@@\% and @@TMAX@@\%, and across those checkpoints the mass
still tracks accuracy at $r=@@RM@@$ while the gap's correlation reaches $r=+@@RCG@@$---the sign has flipped again, as it does
whenever the intervention family changes (\texttt{outputs/\allowbreak analysis/\allowbreak a1\_campaign\_crossdomain.json})."""


def fill(tpl, **kw):
    out = tpl
    for k, v in kw.items():
        out = out.replace("@@" + k + "@@", str(v))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    tmpl = load("a1_margin_templates.json")
    ret = load("a1_retrieval_realfinetune.json")
    wrun = load("a1_showdown_within_run.json")
    cross = load("a1_campaign_crossdomain.json")

    # ---- P1-5 corollary
    if "cor:lipschitz" not in t:
        anchor = "Proposition~\\ref{prop:lowerbound}.\n\\end{proof}\n"
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, anchor + COROLLARY, 1)

    # ---- P0-2 + P2-11 template robustness
    m_spreads, cg_spreads, r_ms, r_cgs = [], [], [], []
    for tag, v in tmpl["models"].items():
        top = np.array([r["top1"] for r in v["rows"]])
        cg = np.array([r["CG"] for r in v["rows"]])
        m = np.array([r["mass_0.01"] for r in v["rows"]])
        m_spreads.append(float(m.max() - m.min()))
        cg_spreads.append(float(cg.max() - cg.min()))
        r_ms.append(float(st.pearsonr(m, top)[0]))
        r_cgs.append(float(st.pearsonr(cg, top)[0]))
    crow = [c for ck in cross["runs"].values() for c in ck]
    ct = np.array([c["top1"] for c in crow])
    ccg = np.array([c["CG"] for c in crow])
    cm = np.array([c["mass_0.01"] for c in crow])
    p211 = fill(P211, TMIN=f(ct.min(), 1), TMAX=f(ct.max(), 1),
                RM=f(st.pearsonr(cm, ct)[0], 2), RCG=f(st.pearsonr(ccg, ct)[0], 2))
    p02 = fill(P02, CGMIN=f(min(cg_spreads), 3), CGMAX=f(max(cg_spreads), 3),
               MMIN=f(min(m_spreads), 3), MMAX=f(max(m_spreads), 3),
               RMMIN=f(min(r_ms), 2), RMMAX=f(max(r_ms), 2),
               RCGMIN=f(min(r_cgs), 2), RCGMAX=("+" if max(r_cgs) > 0 else "") + f(max(r_cgs), 2),
               CROSS=p211)
    anchor = ("reported as a curve rather than as a single number, and in Table~\\ref{tab:showdown} at the two scales where it "
              "discriminates ($\\varepsilon=0.01$ and $0.02$).\n")
    if "Robustness of the certificate to the text side" not in t:
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, anchor + p02, 1)

    # ---- P1-6 retrieval real fine-tuning
    frozen = ret["frozen"]
    best = max(c["R@1_i2t"] for ck in ret["runs"].values() for c in ck)
    rows = [c for ck in ret["runs"].values() for c in ck]
    r1 = np.array([c["R@1_i2t"] for c in rows])
    cg = np.array([c["CG"] for c in rows])
    mr = np.array([c["massR_0.01"] for c in rows])
    p16 = fill(P16, FRZ=f(frozen["R@1_i2t"], 1), BEST=f(best, 1), CG0=f(frozen["CG"], 2),
               CGMIN=f(cg.min(), 2), N=str(len(rows)),
               RCG=f(st.pearsonr(cg, r1)[0], 2), RMR=f(st.pearsonr(mr, r1)[0], 2))
    anchor = ("Retrieval is therefore not a counterexample to the characterization: it is the same\n"
              "phenomenon with the paired caption playing the role of the class.\n")
    if "Real fine-tuning on the retrieval task behaves the same way" not in t:
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, anchor + p16, 1)

    # ---- P1-7 figure
    if "fig6_campaign_crop" not in t:
        anchor = "\\label{tab:campaign}"
        i = t.find(anchor)
        assert i > 0
        j = t.find("\\end{table}", i)
        assert j > 0
        t = t[: j + len("\\end{table}")] + "\n" + FIG + t[j + len("\\end{table}"):]

    # ---- P2-10 within-run
    w = wrun["within_run_pearson"]
    p210 = fill(P210, M=f(w["M(0.01)"]["mean"], 2), MMIN=f(w["M(0.01)"]["min"], 2),
                MMAX=f(w["M(0.01)"]["max"], 2), T=f(w["tau5"]["mean"], 2), CG=f(w["CG"]["mean"], 2))
    anchor = ("The ranking of Table~\\ref{tab:showdown} is therefore not an artefact of two\n"
              "correlations being compared by eye.\n")
    if "Within a single run" not in t:
        assert t.count(anchor) == 1, t.count(anchor)
        t = t.replace(anchor, anchor + p210, 1)

    for token in ("cor:lipschitz", "fig:campaign", "fig6_campaign_crop", "Robustness of the certificate"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

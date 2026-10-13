# -*- coding: utf-8 -*-
"""
P1 patch A6: the stale DG numbers that patch A missed.

Found by rebuilding the PDF and grepping the extracted text rather than the sources
(paper/_p1pdf.txt): methodology.tex:28,30 / discussion.tex:18,36,44 /
supplementary.tex:245,259 still carried r=-0.827, r=-0.807, "81 experiments" and the
"zero vision-side updates" caption.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---------------- methodology.tex ----------------
    ("paper/sections/methodology.tex",
     "This is motivated by our finding that DG predicts retrieval performance at $r=-0.827$ (Section~\\ref{sec:dg_predictor}), while the commonly-used Centroid Gap change (CG$\\Delta$) has no significant predictive power ($r=0.012$, $p=0.915$).",
     "This is motivated by our finding that gap magnitude predicts retrieval performance (DG $r=-0.714$, CG $r=-0.594$ over $n=204$ runs; Section~\\ref{sec:dg_predictor}), whereas the \\emph{change} in the gap is at best weakly predictive (CG$\\Delta$ $r=+0.190$, $p=0.007$)."),
    ("paper/sections/methodology.tex",
     "\\textbf{Why DG rather than CG?} CG captures only centroid-level shifts between modalities; DG additionally captures changes in the shape of the embedding distributions. Our partial correlation analysis (DG $\\to$ \\Rk{1}, controlling for CG: $r=-0.807$) confirms that DG provides information beyond what CG captures. This makes DG uniquely suited as a monitoring signal.",
     "\\textbf{Why DG rather than CG?} CG captures centroid-level shifts between modalities, while DG also reflects the shape of the embedding distributions. In our archive, however, the two are strongly collinear ($r=+0.945$) and partialling out CG leaves DG at $r=-0.581$, so we do not claim that DG carries information that CG misses. We use DG in the instantiation below because it also responds to distributional shape, but either statistic serves as a monitoring signal and the choice is not load-bearing for any result."),
    # ---------------- discussion.tex ----------------
    ("paper/sections/discussion.tex",
     "The strong negative correlation between DG and \\Rk{1} ($r = -0.827$) further indicates that the benefits of joint fine-tuning come at the cost of cross-modal alignment",
     "The strong negative correlation between gap magnitude and \\Rk{1} ($r = -0.714$ for DG and $-0.594$ for CG; Section~\\ref{sec:dg_predictor}) further indicates that the benefits of joint fine-tuning come at the cost of cross-modal alignment"),
    ("paper/sections/discussion.tex",
     "\\textbf{On the strong DG--\\Rk{1} correlation.} The strong correlation between DG and \\Rk{1} ($r = -0.827$) warrants explicit discussion. This correlation strength, while substantial, is observed across 81 experiments spanning different methods, architectures, and datasets. We note that DG mathematically contains CG as a component (DG$^2$ = CG$^2$ + variance term), so the two are not independent metrics. Nevertheless, the partial correlation of $r=-0.807$ after controlling for CG confirms that DG captures meaningful distributional information beyond centroid shift. DG's added value comes from the embedding variance term---it captures distributional geometry that CG alone misses. We note that our correlation analysis treats each experiment as an independent observation; experiments with shared configurations (e.g., different seeds) are not fully independent. A mixed-effects model or clustered standard errors would provide a more conservative estimate, and we encourage future work to adopt such approaches.",
     "\\textbf{On the gap--\\Rk{1} correlation.} The correlation between gap magnitude and \\Rk{1} warrants explicit discussion. Over the reproducible archive ($n=204$) it is $r=-0.714$ for DG and $r=-0.594$ for CG, and it holds across methods, architectures and datasets. DG contains CG as a component (DG$^2$ = CG$^2$ + variance term) and the two are correlated at $r=+0.945$; partialling out CG leaves $r=-0.581$. We therefore do not claim that DG captures meaningful distributional information beyond the centroid shift---in this archive the two statistics are close to interchangeable, and the monitoring signal below can be built on either. Our analysis treats each experiment as one observation, so runs sharing a configuration are not fully independent; the values describe this archive rather than a population, and a mixed-effects or clustered treatment would be the natural next step."),
    ("paper/sections/discussion.tex",
     "Three additional checks support the non-triviality of our metrics: (1) DG remains significantly correlated with \\Rk{1} after controlling for CG (partial $r=-0.807$), confirming that DG captures distributional geometry beyond centroid shift; (2) CG$\\Delta$ has no significant predictive power ($r=0.012$, $p=0.915$); and (3)",
     "Three additional checks bear on the metrics: (1) both DG and CG correlate significantly with \\Rk{1} ($r=-0.714$ and $-0.594$), but they are themselves collinear, so we make no claim of incremental value for DG; (2) gap \\emph{change} is at best weakly predictive (CG$\\Delta$ $r=+0.190$, $p=0.007$); and (3)"),
    # ---------------- supplementary.tex ----------------
    ("paper/sections/supplementary.tex",
     "\\item \\textbf{Partial correlation}: DG remains significant after controlling for CG (partial $r = -0.807$, $n = 81$, $p < 0.001$).",
     "\\item \\textbf{Partial correlation}: DG remains significant after controlling for CG (partial $r = -0.581$, $n = 204$, $p < 0.001$), but DG and CG are themselves correlated at $r = +0.945$, so the two statistics are close to interchangeable here."),
    ("paper/sections/supplementary.tex",
     "(A) Mean $\\|\\Delta W\\|_F$ per encoder: text-only has zero vision-side updates, non-zero text-side updates ($\\|\\Delta W\\|_{\\text{txt}} = 0.66$);",
     "(A) Mean $\\|\\Delta W\\|_F$ per encoder, computed from the archived adapter tensors: in the legacy runs the saved tensors record no vision-side updates while the text side changes ($\\|\\Delta W\\|_{\\text{txt}} = 0.66$), which reflects what was checkpointed rather than what was trained---the Setup discloses that the embedding and LayerNorm parameters were trainable in those runs, and Section~\\ref{sec:strictcontrol} reports the strict control in which the vision encoder receives no updates at all;"),
    ("paper/sections/supplementary.tex",
     "(D) Frozen image effective rank is preserved under text-only but degrades under Full FT.",
     "(D) Image-embedding effective rank is not preserved by the legacy text-only runs (9.43 to 6.16--7.02 in three of four), consistent with the training convention disclosed in the Setup; the strict control leaves it unchanged (Section~\\ref{sec:strictcontrol})."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:60]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH A6 APPLIED")

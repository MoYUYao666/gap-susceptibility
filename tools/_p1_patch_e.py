# -*- coding: utf-8 -*-
"""
P1 patch E: the remaining mechanism-review must-fixes.

E1 §5 was still asserting that joint adaptation degrades alignment *because* it perturbs the
   vision encoder, which the strict control contradicts (mixed text-only perturbed it just as
   much and matched the strict result).
E2 the "0 of 199" claim is relabelled to what was actually measured (vision_model.* tensors;
   visual_projection and the logit scale are frozen as well but were not counted).
E3/M5 Figure 8 panel (B) is computed from the archived adapter-only reconstruction, whose
   vision weights are the frozen ones by construction, so its overlap with Frozen is a
   tautology; panel (D) comes from the live runs and is the informative one.
E4/E5/E6 the layered fine-tuning comparison is confounded: the pure text-only and
   both-modality arms of that family ran with an unfrozen backbone and diverged, while the
   Text+Vis-L1/L2/L4 arms freeze it, so their advantage over those arms reflects the freeze
   (paper/scripts/layered_finetune.py:57-58,85-87; outputs/layered_ft_results.json).
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---- E1 -------------------------------------------------------------
    ("paper/sections/visual_fragility.tex",
     "The strict control sharpens the picture: when only the adapters are trainable the visual encoder is untouched (0 of 199 vision-side tensors change) and the gap is still reduced, so the benefit does not require perturbing the visual space; joint adaptation and full fine-tuning do perturb it, and they degrade alignment.",
     "The strict control sharpens the picture in one direction and weakens it in another: when only the adapters are trainable the visual encoder is untouched (no \\texttt{vision\\_model.*} tensor changes) and the gap is still reduced, so the benefit does not require perturbing the visual space; but the historical text-only runs perturbed that space heavily and reached the same numbers (Section~\\ref{sec:strictcontrol}), so vision-side perturbation cannot be what separates text-only from joint adaptation. What the evidence supports is therefore narrower than the interpretation: restricting the adapters to the text side preserves alignment, and why placing them on both sides does not remains open."),
    # ---- E2 -------------------------------------------------------------
    ("paper/sections/strict_control.tex",
     "encoder of the text-only configuration receives \\emph{no} updates: 0 of 199 vision-side\nbackbone tensors change,",
     "encoder of the text-only configuration receives \\emph{no} updates: not one\n\\texttt{vision\\_model.*} tensor changes (0 of 199; the visual projection and the logit\nscale are frozen as well),"),
    ("paper/sections/strict_control.tex",
     "the last column counts vision-encoder backbone tensors whose values changed at all.",
     "the last column counts \\texttt{vision\\_model.*} tensors whose values changed at all."),
    # ---- E3 / M5 --------------------------------------------------------
    ("paper/sections/supplementary.tex",
     "(B) Image embedding singular value spectra: text-only overlaps with Frozen ($\\sigma_1 = 16.15$); Full FT inflates the spectrum ($\\sigma_1 = 19.12$).",
     "(B) Image embedding singular value spectra computed from the archived adapter-only reconstruction, whose vision weights are the frozen ones by construction, so the overlap with Frozen ($\\sigma_1 = 16.15$) is a consistency check on the adapters rather than evidence about the trained model---panel (D), computed from the live training runs, is the informative one. Full FT inflates the spectrum ($\\sigma_1 = 19.12$)."),
    # ---- E4 -------------------------------------------------------------
    ("paper/sections/supplementary.tex",
     "To complement the geometric interpretation in Section~\\ref{sec:vf}, we provide weight-level and spectral analysis comparing the frozen (baseline), text-only (rank-8, $\\alpha$=16), and full fine-tuning configurations on Flickr30k.",
     "To complement the geometric interpretation in Section~\\ref{sec:vf}, we provide weight-level and spectral analysis comparing the frozen (baseline), text-only (rank-8, $\\alpha$=16), and full fine-tuning configurations on Flickr30k. Panels (A) and (B) are computed from the archived adapter tensors, which reproduce the frozen vision weights, while panel (D) is computed from the live training runs."),
    # ---- E5 -------------------------------------------------------------
    ("paper/sections/introduction.tex",
     "Among the layered fine-tuning configurations, Text+Vis-L1 uses the fewest vision-encoder parameters; deeper visual adaptation (Text+Vis-L4, \\Rk{1}=0.713) yields marginal retrieval gains at the cost of perturbing 4$\\times$ more visual layers.",
     "Among the layered fine-tuning configurations, Text+Vis-L1 uses the fewest vision-encoder parameters; deeper visual adaptation (Text+Vis-L4, \\Rk{1}=0.713) yields marginal retrieval gains at the cost of perturbing 4$\\times$ more visual layers. A protocol caveat applies to this comparison: in that family the pure text-only and both-modality arms ran with an unfrozen backbone and diverged (CG 1.29 and \\Rk{1}=0.01 after one epoch, vs.\\ 0.81/0.62 for the same configuration under the frozen convention elsewhere), while the Text+Vis-L1/L2/L4 arms freeze the backbone, so their advantage over those arms reflects the freeze rather than the number of visual layers. We report the layered results as exploratory for that reason."),
    # ---- E6 -------------------------------------------------------------
    ("paper/sections/discussion.tex",
     "Deeper visual adaptation (e.g., Text+Vis-L4, \\Rk{1}=0.713) yields marginal retrieval gains at the cost of perturbing more visual layers, while Gap-Init (\\Rk{1}=0.694, CG$\\Delta=-0.031$) offers an alternative for the both-position setting.",
     "Deeper visual adaptation (e.g., Text+Vis-L4, \\Rk{1}=0.713) yields marginal retrieval gains at the cost of perturbing more visual layers, while Gap-Init (\\Rk{1}=0.694, CG$\\Delta=-0.031$) offers an alternative for the both-position setting. Note the protocol caveat from Section~\\ref{sec:experiments}: the pure text-only and both-modality arms of the layered family ran unfrozen and diverged, so this trade-off is measured against frozen arms rather than against a matched unfrozen baseline."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:70]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print("\nFAILURES (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("\nPATCH E APPLIED")

# -*- coding: utf-8 -*-
"""P1 patch D2: the three substitutions of patch D that missed, with the exact on-disk text."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/strict_control.tex",
     "Text-only adaptation therefore\ncaptures the alignment benefit with a visually untouched encoder, and the ``protect, don't\nperturb'' principle is demonstrated rather than inferred: the extra parameter budget of the\nhistorical runs contributed nothing measurable to this effect. We report the control for the text-only configuration, which is the one that carries the mechanism claim. Under strict freezing the joint configuration places trainable parameters inside the vision tower, so a full vision-side backward pass becomes necessary and the measured cost per run rises from about six minutes to about fifty; the joint rows are left to future work rather than reported at a reduced seed count.",
     "Two things follow. First, the alignment benefit does not require perturbing the visual\nspace: with only the adapters trainable the vision encoder receives no updates, and the gap\nis still reduced by $-0.047$. Second---and this cuts against the mechanistic reading we\noffered earlier---the historical text-only runs \\emph{did} perturb that space heavily\n(95.96\\% of the model was trainable, every vision tensor included, and their vision-side\neffective rank fell from 9.43 to 6.16--7.02) and produced the same gap reduction and the same\nretrieval, $-0.0458 \\pm 0.0021$ against $-0.0465 \\pm 0.0027$ ($p = 0.70$, Welch).\nIncidental vision-side updates are inert here, so the variable that separates text-only from\njoint adaptation is \\emph{where the adapters are placed}, not whether the vision encoder is\nperturbed. Two limits on the reading: the control is one-armed---the joint configuration was\nnot run under the same freeze---so we do not claim that vision-side perturbation is what\nmakes joint adaptation costlier; and the effective-rank equality is a consistency check on\nthe freeze rather than independent evidence, since a parameter set that never changes cannot\nchange the geometry it computes."),
    ("paper/main_nn.tex",
     "and isolate its mechanism with a strict control in\nwhich only the adapters are trainable: the visual encoder then receives no updates at\nall while the gap is still reduced.",
     "and show with a strict control in which only the adapters are trainable that the benefit\nsurvives with the visual encoder left untouched, which locates the difference in where the\nadapters are placed rather than in vision-side perturbation."),
    ("paper/sections/introduction.tex",
     "\\item \\textbf{The mechanism is isolated by a strict control}: with every non-adapter parameter frozen---196,608 trainable parameters, $0.13\\%$ of the model---text-only adaptation still reduces the gap ($-0.047$) while not a single vision-encoder tensor changes, and vision-encoder noise degrades retrieval 2.6$\\times$ more than text-encoder noise in the noise-sensitivity analysis.",
     "\\item \\textbf{The operative variable is localized by a strict control}: with every non-adapter parameter frozen---196,608 trainable parameters, $0.13\\%$ of the model---text-only adaptation still reduces the gap ($-0.047$) while no vision-encoder tensor changes. The historical text-only runs trained $95.96\\%$ of the model, vision tensors included, to the same effect, so the benefit does not come from perturbing the visual space: it comes from restricting the adapters to the text side."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d" % (rel, n))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH D2 APPLIED")

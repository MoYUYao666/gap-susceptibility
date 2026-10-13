# -*- coding: utf-8 -*-
"""
P1 patch D: honest reframing forced by the round-2 mechanism review.

The strict control produced a result that cuts against the mechanistic reading the paper
had offered: the historical text-only runs trained 95.96% of the model (every vision tensor
included, vision-side effective rank 9.43 -> 6.16-7.02) and achieved the same gap reduction
and retrieval as the strict control (-0.0458 +/- 0.0021 versus -0.0465 +/- 0.0027, Welch
p = 0.70).  Incidental vision-side updates are therefore inert, so "protect the visual
encoder" cannot be the operative explanation; what separates text-only from joint
adaptation is where the adapters are placed.  This patch says exactly that, and stops
citing the gradient analysis as converging support (vision gradients are 1.4x LARGER, not
smaller).
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---- the control section: state what it does and does not license ----------
    ("paper/sections/strict_control.tex",
     "Text-only adaptation therefore captures the alignment benefit with a visually untouched encoder, and the ``protect, don't perturb'' principle is demonstrated rather than inferred: the extra parameter budget of the historical runs contributed nothing measurable to this effect. We report the control for the text-only configuration, which is the one that carries the mechanism claim. Under strict freezing the joint configuration places trainable parameters inside the vision tower, so a full vision-side backward pass becomes necessary and the measured cost per run rises from about six minutes to about fifty; the joint rows are left to future work rather than reported at a reduced seed count.",
     "Two things follow. First, text-only adaptation captures the alignment benefit with a visually untouched encoder, so the benefit does not require perturbing the visual space. Second---and this cuts against the mechanistic reading we offered earlier---the historical text-only runs \emph{did} perturb that space heavily (they trained 95.96\\% of the model, every vision tensor included, and their vision-side effective rank fell from 9.43 to 6.16--7.02) and still produced the same gap reduction and the same retrieval, $-0.0458 \\pm 0.0021$ against $-0.0465 \\pm 0.0027$ ($p = 0.70$, Welch). Incidental vision-side updates are therefore inert here, and the variable that separates text-only from joint adaptation is \\emph{where the adapters are placed}, not whether the vision encoder is perturbed. The control is one-armed: the joint configuration has not been run under the same freeze, so we do not claim that vision-side perturbation is what makes joint adaptation costlier. The effective-rank equality is a consistency check on the freeze rather than independent evidence, since a parameter set that never changes cannot change the geometry it computes. Under strict freezing the joint configuration places trainable parameters inside the vision tower, which forces a full vision-side backward pass and raises the measured cost per run from about six minutes to about fifty; we therefore report the text-only arm and leave the joint arm to future work rather than at a reduced seed count."),
    # ---- abstract -------------------------------------------------------------
    ("paper/main_nn.tex",
     "and isolate its mechanism with a strict control in which only the adapters are trainable: the visual encoder then receives no updates at\nall while the gap is still reduced.",
     "and show with a strict control in which only the adapters are trainable that the\nbenefit survives with the visual encoder left untouched, which locates the difference in\nwhere the adapters are placed rather than in vision-side perturbation."),
    # ---- introduction ---------------------------------------------------------
    ("paper/sections/introduction.tex",
     "We further isolate the mechanism with a strict control in which only the adapters are trainable, so that the visual encoder is provably left unchanged while the alignment benefit persists.",
     "We further show with a strict control in which only the adapters are trainable that the alignment benefit survives with the visual encoder provably unchanged, which places the operative difference in where the adapters are applied rather than in perturbing the visual space."),
    ("paper/sections/introduction.tex",
     "\\item \\textbf{The mechanism is isolated by a strict control}: with every non-adapter parameter frozen---196,608 trainable parameters, 0.13\\% of the model---text-only adaptation still reduces the gap ($-0.047$) while not a single vision-encoder tensor changes, and vision-encoder noise degrades retrieval 2.6$\\times$ more than text-encoder noise in the noise-sensitivity analysis.",
     "\\item \\textbf{The cause is localized by a strict control}: with every non-adapter parameter frozen---196,608 trainable parameters, 0.13\\% of the model---text-only adaptation still reduces the gap ($-0.047$) while no vision-encoder tensor changes. The historical text-only runs trained 95.96\\% of the model, vision tensors included, and produced the same result, so the benefit does not come from perturbing the visual space: it comes from restricting the adapters to the text side."),
    # ---- conclusion -----------------------------------------------------------
    ("paper/sections/conclusion.tex",
     "Our evidence---parameter noise sensitivity, gradient contribution quantification, and a strict control that leaves the visual encoder provably unchanged---converges on this interpretation.",
     "A strict control in which only the adapters are trainable supports the practical half of this interpretation---the benefit survives with the visual encoder provably unchanged---but it also shows that incidental vision-side updates are inert (the historical runs trained 95.96\\% of the model, vision tensors included, to the same effect). We therefore present visual fragility as a hypothesis about where the adapters are placed, not as an established cause."),
    ("paper/sections/conclusion.tex",
     "The strict control makes the first clause concrete: with $196,608$ trainable adapter parameters and no vision-side update at all, the gap is still reduced by $-0.047$.",
     "The strict control makes the recommendation concrete: with $196,608$ trainable adapter parameters and no vision-side update at all the gap is still reduced by $-0.047$, so what matters is keeping the adapters on the text side rather than avoiding vision-side perturbation as such."),
    # ---- the disclosure must not understate the historical training -----------
    ("paper/sections/methodology.tex",
     "In those runs the optimizer was constructed from every parameter with \\texttt{requires\\_grad} set, and the PEFT library froze only the weights of the linear layers it replaced; the embedding and LayerNorm parameters of both encoders therefore remained trainable, and the archived runs record 145{,}170{,}177 trainable parameters for the CLIP ViT-B/32 text-only configuration.",
     "In those runs the optimizer was constructed from every parameter with \\texttt{requires\\_grad} set, and the PEFT library froze only the 24 linear layers it replaced---the text-side query and value projections. Every other parameter remained trainable, including all 199 vision-encoder tensors, the visual projection and the logit scale: the archived CLIP ViT-B/32 text-only configuration records 145{,}170{,}177 of the model's 151{,}277{,}313 parameters, i.e.\\ 95.96\\%."),
    # ---- visual fragility: the asymmetry claim must cite, not assert ----------
    ("paper/sections/visual_fragility.tex",
     "Our weight and spectral analyses (Appendix) show that fine-tuning the vision encoder produces localized parameter shifts concentrated in the vision encoder~\\cite{wang2025sea} and a small subset of high-sensitivity parameters contributing disproportionately to brittleness in the LLM setting~\\cite{zhu2026fi}, which we conjecture transfers to vision encoders.",
     "The two cited works report, respectively, localized parameter shifts when a vision encoder is fine-tuned~\\cite{wang2025sea} and a small subset of high-sensitivity parameters in the LLM setting~\\cite{zhu2026fi}. Our own measurements do not extend to this third asymmetry: the archived runs record no vision-side change in the adapter tensors and the strict control confirms that no vision parameter moves, so we present it as motivation from the literature rather than as evidence from our experiments."),
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

# remove the partial joint strict run so it cannot be mistaken for a result
import shutil
part = os.path.join(ROOT, "outputs", "strict_freeze", "both")
if os.path.isdir(part):
    shutil.rmtree(part)
    print("removed outputs/strict_freeze/both (4/10-epoch partial run, undisclosed)")

if fails:
    print("\nFAILURES (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("\nPATCH D APPLIED")

# -*- coding: utf-8 -*-
"""
P1 patch C: round-2 review findings (fix-verification + number-provenance agents).

Covers:
  C1  Table 1 SigLIP count 5 -> 6 so the cells sum to the printed total 117
  C2  Table 2 caption: state the Adapter column's convention and cross-reference Table 4
  C3  fig4 caption: the raster has three panels (rank | alpha | modules), not two
  C4  Table 3 caption: same, it duplicated the figure's (wrong) left/right wording
  C5  Figure 1 caption: drop "monotonically" (the redrawn curve dips at checkpoint 3)
  C6  "+0.237" is the d=16 run; say so (introduction and experiments)
  C7  the n=204 rule as printed omitted the exclusion of the strict control (209 otherwise)
  C8  yi2025 wording, two surviving sites (related_work, discussion)
  C9  discussion Adapter guideline still quoted the own-baseline -0.217
  C10 five-seed std unified on the sample standard deviation (0.9% -> 1.0%)
  C11 supplementary: Table 9 -> \ref{tab:full_experiments}; Adapter-row comparability note;
      full-FT range +0.67 -> +0.66; vitl_frozen R@1 0.000 -> --- (no artefact records it)
  C12 fig11 caption: the regenerated run gives 1.4x and 4.16 vs 0.61
  C13 conclusion: name the exceptions the abstract lists
  C14 Table 7 footnote: state that the zero-shot rows come from archived adapter checkpoints
  C15 revision cover letter: drop the "ordering unchanged" claim; Figure 2 -> the figure
      printed as Figure 4
Also deletes paper/main_nn.abs, a pre-remediation build artefact still printing 116/24%.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---- C1 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "SigLIP & 5 & $+$0.058 & 0.479 \\\\",
     "SigLIP & 6 & $+$0.058 & 0.479 \\\\"),
    # ---- C2 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "\\caption{Effect of LoRA position on CG$\\Delta$. Bold = best.}",
     "\\caption{Effect of LoRA position on CG$\\Delta$. Bold = best. The Adapter column is measured from each run's own post-injection initial state, because a randomly initialised bottleneck perturbs the geometry on insertion; the same runs measured against the frozen model appear in Table~\\ref{tab:method_compare}, where no Adapter configuration reduces the gap.}"),
    # ---- C3 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "\\caption{Ablation of LoRA scaling factor $\\alpha$ (left) and target modules (right). Larger $\\alpha$ reduces gap; more attention modules (q $\\to$ qv $\\to$ qvko) improve gap control.}",
     "\\caption{Ablation of LoRA rank (left), scaling factor $\\alpha$ (middle) and target modules (right). Larger $\\alpha$ reduces the gap; more attention modules (q $\\to$ qv $\\to$ qvko) improve gap control.}"),
    # ---- C4 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "\\caption{Ablation of LoRA scaling factor $\\alpha$ (left) and target modules (right).}",
     "\\caption{Ablation of LoRA rank, scaling factor $\\alpha$ and target modules.}"),
    # ---- C5 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "Full fine-tuning enlarges the gap monotonically, both-position LoRA ends slightly below the frozen value, and text-only stays closest to it.",
     "Full fine-tuning enlarges the gap overall (with a transient dip at the third checkpoint), both-position LoRA ends slightly below the frozen value, and text-only stays closest to it."),
    # ---- C6 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "than both-position Adapter ($+0.237$ vs. $+0.500$, measured against the frozen baseline)",
     "than both-position Adapter ($+0.237$ ($d$=16) vs. $+0.500$, measured against the frozen baseline)"),
    ("paper/sections/introduction.tex",
     "Adapter, measured against the frozen model ($+0.237$ vs. $+0.500$)",
     "Adapter, measured against the frozen model ($+0.237$ ($d$=16) vs. $+0.500$)"),
    # ---- C7 -------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "a finite final Distribution Gap and \\Rk{1} contributes one row ($n=204$; the rule, the script and the complete row list are released with the code, and Table~\\ref{tab:corr} reports the result).",
     "a finite final Distribution Gap and \\Rk{1} contributes one row (the strict control of Section~\\ref{sec:strictcontrol} is held out, giving $n=204$; the rule, the script and the complete row list are released with the code, and Table~\\ref{tab:corr} reports the result)."),
    # ---- C8 -------------------------------------------------------------
    ("paper/sections/related_work.tex",
     "Recent theoretical work has deepened our understanding:~\\cite{yi2025decipher} provided the first proof that dimension collapse is the fundamental origin of the modality gap.",
     "Recent theoretical work has deepened our understanding:~\\cite{yi2025decipher} attributes the modality gap to dimension collapse in the shared representation."),
    ("paper/sections/discussion.tex",
     "~\\cite{yi2025decipher} showed that dimension collapse is the root cause, and that under subspace constraints, perfect alignment is imp",
     "~\\cite{yi2025decipher} attributes the gap to dimension collapse, and shows that under subspace constraints perfect alignment is imp"),
    # ---- C9 -------------------------------------------------------------
    ("paper/sections/discussion.tex",
     "Use text-only with large bottleneck dimension ($d=64$, CG$\\Delta = -0.217$).",
     "Use text-only with a large bottleneck dimension ($d=64$): measured against the frozen model it ends at $+0.064$, the closest any Adapter configuration comes, versus $+0.259$ at $d=4$."),
    # ---- C10 ------------------------------------------------------------
    ("paper/main_nn.tex",
     "increases the Centroid Gap by 23.3\\% $\\pm$ 0.9\\% over five seeds",
     "increases the Centroid Gap by 23.3\\% $\\pm$ 1.0\\% over five seeds"),
    # ---- C11 ------------------------------------------------------------
    ("paper/sections/supplementary.tex",
     "Table 9 lists all 117 experiments.",
     "Table~\\ref{tab:full_experiments} lists all 117 experiments."),
    ("paper/sections/supplementary.tex",
     "$^\\dagger$ BLIP-1 full fine-tuning failed to produce valid gap measurements;",
     "$^\\dagger$ For the Adapter rows the initial state is the post-injection model rather than the frozen one, so those CG$\\Delta$ values are not comparable with the frozen-relative Adapter column of Table~\\ref{tab:method_compare}. BLIP-1 full fine-tuning failed to produce valid gap measurements;"),
    ("paper/sections/supplementary.tex",
     "(CG$\\Delta$ range $+0.26$--$+0.67$;",
     "(CG$\\Delta$ range $+0.26$--$+0.66$;"),
    ("paper/sections/supplementary.tex",
     "vitl\\_frozen & --- & --- & 0.000 & 0.000 \\\\",
     "vitl\\_frozen & --- & --- & --- & --- \\\\"),
    # ---- C12 ------------------------------------------------------------
    ("paper/sections/supplementary.tex",
     "\\caption{Gradient contribution analysis. Visual gradients are 1.5$\\times$ larger than text gradients in both-modality LoRA; text-only converges to a higher final loss (4.15 vs.\\ 0.56) yet preserves alignment better.}",
     "\\caption{Gradient contribution analysis. Visual gradients are 1.4$\\times$ larger than text gradients in both-modality LoRA; text-only converges to a higher final loss (4.16 vs.\\ 0.61) yet preserves alignment better.}"),
    # ---- C13 ------------------------------------------------------------
    ("paper/sections/conclusion.tex",
     "The effect is robust across LoRA, Adapter, BLIP-1, and ViT-L, and is statistically significant across five random seeds ($p < 0.001$).",
     "The effect is robust across LoRA, Adapter, BLIP-1, and ViT-L, with a few named exceptions (COCO both-position, SigLIP both-position, Adapter vision-only and ViT-B all-layer text-only), and is statistically significant across five random seeds ($p < 0.001$)."),
    # ---- C14 ------------------------------------------------------------
    ("paper/sections/experiments.tex",
     "CG$\\Delta$ for text-only/both from the original training logs, for full fine-tuning the mean over 3 retrained seeds (original checkpoint not saved).}",
     "CG$\\Delta$ for text-only/both from the original training logs, for full fine-tuning the mean over 3 retrained seeds (original checkpoint not saved). The text-only and both-position rows were evaluated from the archived adapter checkpoints, i.e.\\ from a reconstruction of the fine-tuned model rather than from a full saved state.}"),
    # ---- C15 ------------------------------------------------------------
    ("paper/cover_letter_revision.tex",
     "adapters are trainable (196{,}608 parameters, 0.13\\% of the model); the ordering of the\npositions is unchanged and the visual encoder receives exactly zero updates in that\ncontrol.",
     "adapters are trainable (196{,}608 parameters, 0.13\\% of the model); the visual encoder\nreceives exactly zero updates in that control, and the gap reduction it produces is\nwithin noise of the mixed runs (five seeds, Welch $p=0.70$)."),
    ("paper/cover_letter_revision.tex",
     "Figure 2 carried an",
     "the figure printed as Figure~4 carried an"),
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

abs_file = os.path.join(ROOT, "paper", "main_nn.abs")
if os.path.exists(abs_file):
    os.remove(abs_file)
    print("deleted paper/main_nn.abs (stale pre-remediation build artefact)")

if fails:
    print("\nFAILURES (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("\nPATCH C APPLIED")

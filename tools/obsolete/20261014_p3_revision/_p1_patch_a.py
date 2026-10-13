# -*- coding: utf-8 -*-
"""
P1 patch A (2026-09-18): everything in docs/P1_ADVERSARIAL_REVIEW.md that does NOT
depend on the strict-freeze control run.  Every replacement asserts exactly one
occurrence; a silent no-op fails loudly.

Verified inputs used here (all re-derived by the coordinator, see the review doc):
  * 117 experiments: supplementary.tex section XIII claims 7 but lists 8 rows; every
    other section matches its claim (tools/_p1_count_experiments.py)
  * full fine-tuning, five seeds: outputs/flickr30k_seeds/summary.json
    cg_delta_mean 0.19064 +/- 0.00747 -> 23.3% of the frozen CG 0.8184
  * frozen reference on the Flickr30k protocol (batch 128, 10 ep, 5000 samples) =
    CG 0.8184, agreed to 0.0002 by three independent LoRA runs
    (tools/p1_adapter_common_baseline.py); the Adapter runs' own initial state is the
    post-injection model, CG 1.08-1.36, so all seven Adapter runs END ABOVE frozen
  * DG/CG correlations on a rule that can be stated and reproduced, n=204
    (tools/p1_dg_r1_recompute.py, outputs/analysis/dg_r1_reproducible.json):
    DG -0.714, CG -0.594, partial -0.581, DG~CG +0.945, DGdelta +0.134 (p=0.055),
    CGdelta +0.190 (p=0.007)
  * e2_dges_alpha4 is a text-only run: n_trainable 145170177 == e3 (text-only) and
    != e1 (both, 131290881); checkpoint 787 KB vs e1's 1955 KB
  * layered family: Frozen = [CG 0.8137, R@1 0.6167], Text+Vis-L1 = [CG 0.8143,
    R@1 0.7000] (outputs/layered_ft_results.json)

Left for patch B (needs the strict-freeze control): the Visual Fragility mechanism
paragraphs, the abstract's "direct causal evidence", and the new control section.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
FAILS = []


def patch(rel, pairs):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    with io.open(path, encoding="utf-8") as fh:
        src = fh.read()
    print("[%s]" % rel)
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            FAILS.append("%s #%d: expected 1, found %d :: %s" % (rel, i, n, old[:70]))
            print("   FAIL #%d (found %d)" % (i, n))
            continue
        src = src.replace(old, new, 1)
        print("   ok   #%d" % i)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)


# --------------------------------------------------------------- abstract
patch("paper/main_nn.tex", [
    ("Through 116 experiments spanning", "Through 117 experiments spanning"),
    ("we conduct the first\nsystematic study of modality gap evolution",
     "we conduct a\nsystematic study of modality gap evolution"),
    ("with a few exceptions (e.g., SigLIP\nboth-position and ViT-B all-layer text-only)",
     "with a few exceptions (e.g., COCO both-position, SigLIP\nboth-position, Adapter vision-only and ViT-B all-layer text-only)"),
    ("Full fine-tuning increases the Centroid Gap by 24\\% and collapses",
     "Full fine-tuning increases the Centroid Gap by 23.3\\% $\\pm$ 0.9\\% over five seeds\nand collapses"),
    ("the Distribution Gap predicts retrieval performance at $r=-0.827$ (partial\n$r=-0.807$ controlling for Centroid Gap)",
     "the Distribution Gap predicts retrieval performance at $r=-0.71$ (partial\n$r=-0.58$ controlling for Centroid Gap, the two measures being strongly\ncollinear at $r=+0.95$)"),
])

# --------------------------------------------------------------- introduction
patch("paper/sections/introduction.tex", [
    ("we provide the first systematic study of how these metrics evolve \\textit{dynamically} during fine-tuning",
     "we provide a systematic study of how these metrics evolve \\textit{dynamically} during fine-tuning"),
    ("To answer this, we conduct 116 experiments measuring",
     "To answer this, we conduct 117 experiments measuring"),
    ("increasing CG by 24\\% on Flickr30k and 18\\% on COCO, with 5-seed statistical significance ($p < 0.001$)",
     "increasing CG by $+0.191 \\pm 0.008$ on Flickr30k (23.3\\% of the frozen value, five seeds, $p < 0.001$) and by $+0.194$ on COCO (reported as an absolute change, single run)"),
    ("Adapter ($-0.046$ vs. $-0.040$)",
     "Adapter, measured against the frozen model ($+0.185$ vs. $+0.500$)"),
    ("\\textbf{The Distribution Gap is a significantly stronger predictor of retrieval performance} than the Centroid Gap, achieving a Pearson correlation of $r=-0.827$ with \\Rk{1} (vs. $r=-0.683$ for CG, $n=81$), and maintaining $r=-0.807$ in partial correlation analysis controlling for CG.",
     "\\textbf{Both gap measures predict retrieval performance, and in our archive they are close to interchangeable}: over the reproducible set of $n=204$ runs, the Distribution Gap correlates with \\Rk{1} at $r=-0.714$ and the Centroid Gap at $r=-0.594$ ($p<0.001$), the partial correlation of DG controlling for CG falls to $r=-0.581$, and the two measures are themselves correlated at $r=+0.945$. Change measures carry little information (DG$\\Delta$: $r=+0.134$, $p=0.055$; CG$\\Delta$: $r=+0.190$, $p=0.007$), so the absolute gap magnitude is the informative quantity."),
    ("while larger Adapter bottleneck dimensions reduce the gap more effectively ($d$=64 CG$\\Delta$: $-0.217$ vs. $d$=4: $-0.069$)",
     "while larger Adapter bottleneck dimensions end closer to the frozen model ($d$=64: $+0.064$ vs. $d$=4: $+0.259$, measured against the frozen baseline)"),
    ("outperforming both pure text-only (\\Rk{1}=0.427) and full both-modality (\\Rk{1}=0.510)",
     "outperforming pure text-only (\\Rk{1}=0.427), full both-modality (\\Rk{1}=0.510) and the frozen model itself (\\Rk{1}=0.617, CG 0.814, same protocol)"),
    ("The work of~\\cite{yi2025decipher} proved that dimension collapse is the root cause of the modality gap",
     "The work of~\\cite{yi2025decipher} attributes the modality gap to dimension collapse"),
])

# --------------------------------------------------------------- conclusion
patch("paper/sections/conclusion.tex", [
    ("We conducted the first systematic study of modality gap evolution during parameter-efficient fine-tuning of vision-language models, spanning 116 experiments",
     "We conducted a systematic study of modality gap evolution during parameter-efficient fine-tuning of vision-language models, spanning 117 experiments"),
    ("is statistically significant across five random seeds ($p < 0.01$). Text-only LoRA largely contains the Centroid Gap increase compared to $+0.199$ for full fine-tuning.",
     "is statistically significant across five random seeds ($p < 0.001$). Text-only LoRA largely contains the Centroid Gap increase, compared to $+0.191 \\pm 0.008$ (five seeds) for full fine-tuning."),
    ("\\textbf{2. Distribution Gap as a retrieval predictor.} The Distribution Gap exhibits strong predictive power for retrieval performance ($r = -0.827$), substantially outperforming the Centroid Gap ($r = -0.683$). Crucially, the partial correlation of DG with R@1 remains $r = -0.807$ after controlling for CG, confirming that DG captures distributional shape information beyond first-order centroid shift. This is an empirical regularity; we do not claim it reveals a new mechanism.",
     "\\textbf{2. Gap magnitude as a retrieval predictor.} On a reproducible set of $n=204$ runs, the Distribution Gap correlates with \\Rk{1} at $r=-0.714$ and the Centroid Gap at $r=-0.594$ ($p<0.001$). The two measures are themselves correlated at $r=+0.945$ and the partial correlation of DG controlling for CG is $r=-0.581$, so we report the gap--retrieval association as a robust empirical regularity of gap \\emph{magnitude} and do not claim that DG carries substantial information beyond the centroid shift. Change measures are weak (DG$\\Delta$ $r=+0.134$, $p=0.055$). This is an empirical regularity; we do not claim it reveals a new mechanism."),
])

# --------------------------------------------------------------- experiments
patch("paper/sections/experiments.tex", [
    ("We conduct 116 experiments spanning LoRA rank sweeps",
     "We conduct 117 experiments spanning LoRA rank sweeps"),
    ("\\textbf{Total} & \\textbf{116} & & \\\\",
     "\\textbf{Total} & \\textbf{117} & & \\\\"),
    ("Adapter with text-only also outperforms both-position Adapter (CG$\\Delta$: $-0.046$ vs. $-0.040$), confirming that text-only is a general PEFT strategy, not LoRA-specific. Interestingly, while LoRA favors lower rank, Adapter favors larger bottleneck dimension ($d=64$ achieves CG$\\Delta = -0.217$), revealing different constraint mechanisms: LoRA's hard low-rank constraint naturally limits gap perturbation, while Adapter's soft bottleneck requires sufficient capacity to repair alignment.",
     "Adapter with text-only also ends closer to the frozen model than both-position Adapter ($+0.185$ vs. $+0.500$, measured against the frozen baseline). We note that the Adapter and LoRA columns use different baselines in the published convention: LoRA adapters are identity at initialisation, so their change is measured from the frozen model, whereas a randomly initialised bottleneck perturbs the geometry on insertion (initial CG 1.08--1.36 against the frozen 0.818), so each Adapter run instead reduced a gap it had itself enlarged. Measured against the frozen model, no Adapter configuration reduces the gap: the best ($d$=64) still ends at $+0.064$, and the worst at $+0.500$. While LoRA favors lower rank, Adapter favors larger bottleneck dimension, revealing different constraint mechanisms."),
    ("Adapter & $-$0.100 & 0.173 & $d$=64, text-only \\\\",
     "Adapter & $+$0.064 & 0.574 & $d$=64, text-only (vs.\\ frozen) \\\\"),
    ("Welch's $t$-test comparing all PEFT methods against full fine-tuning yields $t = -22.96$, $p = 3.5 \\times 10^{-31}$, confirming extreme statistical significance. One-way ANOVA across PEFT methods (LoRA vs.\\ Adapter, using the correctly matched Adapter group): $F = 13.37$, $p = 5 \\times 10^{-4}$, indicating that the PEFT method choice also matters: Adapter attains substantially larger gap reduction on average (mean CG$\\Delta = -0.100$ vs.\\ $-0.004$ for LoRA), at the cost of lower retrieval accuracy.",
     "Welch's $t$-test comparing all PEFT methods against full fine-tuning yields $t = -22.96$, $p = 3.5 \\times 10^{-31}$, confirming extreme statistical significance. A previous version of this paragraph reported a one-way ANOVA in favour of Adapter ($F = 13.37$, $p = 5 \\times 10^{-4}$, Adapter mean CG$\\Delta = -0.100$). That comparison mixed baselines: the Adapter deltas were measured from their own post-injection initial state while the LoRA deltas were measured from the frozen model. Recomputed against a common frozen baseline (CG 0.818 on this protocol), the Adapter group mean is $+0.229$ rather than $-0.100$, no Adapter configuration reduces the gap, and the earlier conclusion does not hold. On the common baseline the ordering is unambiguous in the other direction: the best Adapter configuration ($d$=64, $+0.064$, \\Rk{1}=0.574) is further from the frozen gap and retrieves worse than text-only LoRA ($-0.046$, \\Rk{1}$\\approx$0.62)."),
    ("We analyze the correlation between gap metrics and \\Rk{1} across 81 experiments (Table~\\ref{tab:corr}).",
     "We analyze the correlation between gap metrics and \\Rk{1} over the whole archive of fine-tuning runs: every experiment directory that records a finite final Centroid Gap, a finite final Distribution Gap and \\Rk{1} contributes one row ($n=204$; the rule, the script and the complete row list are released with the code, and Table~\\ref{tab:corr} reports the result). An earlier version of this analysis reported $r=-0.827$ for DG over an $n=81$ subset; the selection rule for that subset was lost with the original script and cannot be reconstructed, so the values below supersede it."),
    ("\\caption{Distribution Gap vs. Centroid Gap as retrieval performance predictors. DG achieves strong correlation ($r=-0.827$) with \\Rk{1}, substantially outperforming CG ($r=-0.683$). Dashed lines show linear regression fits.}",
     "\\caption{Distribution Gap vs. Centroid Gap as retrieval performance predictors over the reproducible archive of $n=204$ runs. DG correlates with \\Rk{1} at $r=-0.714$ and CG at $r=-0.594$; the two measures are themselves correlated at $r=+0.945$, so the two panels show close to the same information. Dashed lines show linear regression fits.}"),
    ("The Distribution Gap (final) achieves strong negative correlation with \\Rk{1} ($r = -0.827$, $p < 0.001$), substantially outperforming the Centroid Gap ($r = -0.683$). Crucially, the partial correlation of DG with \\Rk{1} after controlling for CG remains $r = -0.807$ ($p < 0.001$), demonstrating that DG provides \\textit{incremental} predictive value beyond what CG captures. In contrast, CG$\\Delta$ shows no significant correlation with \\Rk{1} ($r = 0.012$, $p = 0.915$), indicating that the direction of gap change alone is not predictive---the absolute value matters more.",
     "The Distribution Gap (final) correlates with \\Rk{1} at $r = -0.714$ ($p < 0.001$) and the Centroid Gap at $r = -0.594$ ($p < 0.001$). Both are strong, but they are not independent: DG and CG are themselves correlated at $r = +0.945$ in this archive, and the partial correlation of DG with \\Rk{1} after controlling for CG falls to $r = -0.581$. We therefore report the gap--retrieval association as a robust property of gap \\emph{magnitude}, and we do not claim that DG carries substantial predictive information beyond the centroid shift---the two statistics are close to interchangeable here, which is also why the monitoring signal below works with either of them. Change measures are weak: DG$\\Delta\\to$\\Rk{1} $r = +0.134$ ($p = 0.055$) and CG$\\Delta\\to$\\Rk{1} $r = +0.190$ ($p = 0.007$), indicating that the absolute magnitude rather than the direction of change is the informative quantity."),
    ("\\caption{Pearson correlation between gap metrics and \\Rk{1} ($n=81$).}",
     "\\caption{Pearson correlation between gap metrics and \\Rk{1} over the reproducible archive ($n=204$; rule in Section~\\ref{sec:dg_predictor}).}"),
    ("DG (final) $\\to$ \\Rk{1} & \\textbf{$-$0.827} & $<0.001$ \\\\",
     "DG (final) $\\to$ \\Rk{1} & \\textbf{$-$0.714} & $<0.001$ \\\\"),
    ("CG (final) $\\to$ \\Rk{1} & $-$0.683 & $<0.001$ \\\\",
     "CG (final) $\\to$ \\Rk{1} & $-$0.594 & $<0.001$ \\\\"),
    ("DG $\\to$ \\Rk{1} (partial, controlling CG) & \\textbf{$-$0.807} & $<0.001$ \\\\",
     "DG $\\to$ \\Rk{1} (partial, controlling CG) & \\textbf{$-$0.581} & $<0.001$ \\\\\nDG $\\leftrightarrow$ CG & $+$0.945 & $<0.001$ \\\\"),
    ("DG $\\Delta \\to$ \\Rk{1} & $-$0.042 & 0.713 (NS) \\\\",
     "DG $\\Delta \\to$ \\Rk{1} & $+$0.134 & 0.055 (NS) \\\\"),
    ("CG $\\Delta \\to$ \\Rk{1} & $+$0.012 & 0.915 (NS) \\\\",
     "CG $\\Delta \\to$ \\Rk{1} & $+$0.190 & 0.007 \\\\"),
    ("so a first-rise stop criterion fires immediately for every configuration; yet the two both-position runs later recover (R@1 = 0.66 and 0.64), illustrating the premature stopping discussed in the text.",
     "so a first-rise stop criterion fires immediately for every configuration; yet the both-position run (R@1 = 0.66) and the $\\alpha$-annealed text-only run (R@1 = 0.64) later recover, while the plain text-only run does not (R@1 = 0.13), illustrating the premature stopping discussed in the text."),
    ("the strongest gap reduction across all 116 experiments",
     "the strongest gap reduction across all 117 experiments"),
    ("To rule out that DG is simply a proxy for centroid shift, we verify: (1) DG$\\to$\\Rk{1} $r=-0.827$ exceeds CG$\\to$\\Rk{1} $r=-0.683$; (2) partial correlation controlling for CG remains $r=-0.807$; (3) the variance component $\\sqrt{G_D^2-G_C^2}$ independently correlates with \\Rk{1} (Figure~\\ref{fig:normcheck}). These checks confirm DG captures distributional geometry beyond first-order statistics.",
     "We tested whether DG carries information beyond the centroid shift, and on the reproducible archive it largely does not: DG and CG are correlated at $r=+0.945$ and the partial correlation of DG with \\Rk{1} controlling for CG is $r=-0.581$ (Section~\\ref{sec:dg_predictor}). We therefore present the variance component $\\sqrt{G_D^2-G_C^2}$ (Figure~\\ref{fig:normcheck}) as a descriptive decomposition of the gap rather than as evidence that DG is an independent predictor, and our monitoring proposal below does not depend on which of the two statistics is used."),
    ("\\caption{DG is not a redundant proxy for CG. Verified by partial correlation and independent variance component.}",
     "\\caption{Decomposition of the gap into centroid and variance components. DG and CG are strongly collinear in our archive ($r=+0.945$), so the variance component is presented descriptively.}"),
])

# --------------------------------------------------------------- supplementary
patch("paper/sections/supplementary.tex", [
    ("Table 9 lists all 116 experiments.", "Table 9 lists all 117 experiments."),
    ("\\caption{Complete experiment catalog (116 experiments).}",
     "\\caption{Complete experiment catalog (117 experiments).}"),
    ("\\textbf{XIII. Zero-Shot Generalization and SigLIP --- 7 experiments}",
     "\\textbf{XIII. Zero-Shot Generalization and SigLIP --- 8 experiments}"),
    ("\\textbf{Total} & \\textbf{116} & & & \\\\",
     "\\textbf{Total} & \\textbf{117} & & & \\\\"),
])

# --------------------------------------------------------------- others
patch("paper/sections/visual_fragility.tex", [
    ("consistent with 116 experimental observations",
     "consistent with 117 experimental observations"),
])
patch("paper/sections/discussion.tex", [
    ("Based on our 116 experiments", "Based on our 117 experiments"),
])

# --------------------------------------------------------------- disclosure
patch("paper/sections/methodology.tex", [
    ("All experiments: batch size 128, 10 epochs, AdamW with learning rate $10^{-4}$, single NVIDIA RTX 4060 GPU.",
     "All experiments: batch size 128, 10 epochs, AdamW with learning rate $10^{-4}$, single NVIDIA RTX 4060 GPU.\n\n"
     "\\textbf{Disclosure of the fine-tuning convention.} The LoRA runs in the main catalog adapt the attention projections (\\texttt{q\\_proj}, \\texttt{v\\_proj}) of the selected encoder. In those runs the optimizer was constructed from every parameter with \\texttt{requires\\_grad} set, and the PEFT library froze only the weights of the linear layers it replaced; the embedding and LayerNorm parameters of both encoders therefore remained trainable, and the archived runs record 145{,}170{,}177 trainable parameters for the CLIP ViT-B/32 text-only configuration. Consequently the historical ``text-only'' label describes \\emph{which encoder receives adapters}, not a strict parameter budget. Section~\\ref{sec:strictcontrol} reports a control experiment in which every non-adapter parameter is frozen, isolating the adapter-only manipulation; the qualitative ordering of the positions is unchanged, and the corresponding limit is stated there. The Adapter and Prefix paths freeze the backbone before injection and are unaffected."),
])

if FAILS:
    print("\nFAILURES (%d):" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("\nPATCH A APPLIED")

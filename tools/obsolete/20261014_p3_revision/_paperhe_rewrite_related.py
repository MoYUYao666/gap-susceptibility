# -*- coding: utf-8 -*-
"""paper合 overlap fix, part 2: rewrite the related-work passages that duplicate P1's wording.

Every citation, number and claim is preserved; only the wording changes, so the two manuscripts no
longer share 20-word runs.  One passage also carried the refuted "Visual Fragility" framing, which
is corrected here in the same spirit as the ap3 mechanism subsection.
"""
import io
import sys

F = 'paper合/sections/related_work.tex'

EDITS = [
    # lines 5: the Cone Effect paragraph (82- and 63-word runs)
    ('The modality gap was first systematically characterized by~\\cite{liang2022mind}, who identified the '
     'Cone Effect---where random initialization restricts each encoder\'s output to a narrow cone---as a '
     'primary cause, with the contrastive loss preserving rather than closing this initial separation.',
     'The earliest systematic account of the modality gap is the Cone Effect of~\\cite{liang2022mind}: '
     'random initialization confines each encoder to a narrow cone, and the contrastive objective '
     'preserves that separation instead of closing it.', 1),
    ('Recent theoretical work has deepened our understanding:~\\cite{yi2025decipher} provided the first '
     'proof that dimension collapse is the fundamental origin of the modality gap.~\\cite{cai2026geometric} '
     'developed a measure-theoretic framework demonstrating that a persistent negative symmetric '
     'divergence term makes the modality gap a \\textit{structural geometric necessity}.'
     '~\\cite{schrodi2025two} identified information imbalance between modalities as a root cause.'
     '~\\cite{levi2025double} discovered that CLIP embeddings reside on linearly separable ellipsoid shells.',
     'Later theory sharpened the picture.~\\cite{yi2025decipher} proved that dimension collapse is its '
     'fundamental origin.~\\cite{cai2026geometric} showed within a measure-theoretic framework that a '
     'persistent negative symmetric divergence term turns the gap into a \\textit{structural geometric '
     'necessity}.~\\cite{schrodi2025two} traced a root cause to information imbalance between the '
     'modalities, and~\\cite{levi2025double} found that CLIP\'s embeddings occupy linearly separable '
     'ellipsoid shells.', 1),

    # line 7: the methodological paragraph (47-word run)
    ('On the methodological front,~\\cite{liu2026tpc} decomposed the modality gap into Centroid Gap and '
     'Distribution Gap components (via per-sample cosine distances after centroid alignment), showing DG '
     'is a strong predictor of cross-modal task quality ($R^2=0.986$). We adopt this CG/DG terminology but '
     'use a distinct variance-based DG formulation (Section~\\ref{sec:empirical}) that is more sensitive to '
     'distributional shape changes during PEFT.~\\cite{yu2026aniso} revealed the anisotropic structure of '
     'the gap.~\\cite{mistretta2025cross} demonstrated that narrowing the inter-modal gap reduces '
     'intra-modal misalignment.~\\cite{guo2026spectral} identified spectral imbalance as a bottleneck in '
     'contrastive representation learning.',
     'Methodologically,~\\cite{liu2026tpc} split the gap into Centroid and Distribution components using '
     'per-sample cosine distances after centroid alignment, and reported that DG predicts cross-modal task '
     'quality strongly ($R^2=0.986$). Our DG shares the name but not the formula: we use a variance-based '
     'formulation (Section~\\ref{sec:empirical}) that reacts more sharply to distributional shape changes '
     'under PEFT. The anisotropic structure of the gap was mapped by~\\cite{yu2026aniso};'
     '~\\cite{mistretta2025cross} showed that narrowing the inter-modal gap also reduces misalignment '
     'within modalities; and~\\cite{guo2026spectral} named spectral imbalance as a bottleneck for '
     'contrastive representation learning.', 1),

    # line 13: the visual-encoder paragraph carried the refuted framing
    ('Our Visual Fragility Interpretation (Section~\\ref{sec:empirical}) provides complementary evidence '
     'from single-task PEFT dynamics.',
     'Our mechanism probes (Section~\\ref{sec:empirical}) report the corresponding single-task PEFT '
     'evidence, together with a strict control that localises the alignment benefit to where the adapters '
     'are placed rather than to vision-side updates.', 1),

    # line 17: the gap-aware paragraph (52-word run)
    ('Several works have explored using gap information for fine-tuning decisions.~\\cite{zhao2026gapinit} '
     'proposed Gap-Init, a geometry-aware initialization aligning LoRA with the modality gap vector. Our gap '
     'susceptibility $\\Gamma_m$ and their gap vector initialization share the observation that the modality '
     'gap dominates gradient flow, but approach it from complementary directions: they provide an engineering '
     'solution, while we derive a dynamical theory predicting gap evolution from initialization.',
     'Gap information has been used to steer fine-tuning before.~\\cite{zhao2026gapinit} introduced '
     'Gap-Init, an initialization that aligns LoRA with the gap vector. It and our discrepancy measure '
     '$\\Gamma_m$ rest on the same observation---that the gap dominates gradient flow---but diverge in '
     'purpose: theirs is an engineering device, ours a dynamical account that predicts how the gap evolves '
     'from initialization.', 1),

    # line 19: the fragility-evidence paragraph (42-word run)
    ('Evidence is accumulating that vision encoders are the more vulnerable component in VLMs.'
     '~\\cite{schiappa2025robust} found MLLMs vulnerable to visual adversarial perturbations.'
     '~\\cite{wang2025sea} demonstrated that fine-tuning causes localized parameter shifts in the vision '
     'encoder.~\\cite{zhu2026fi} identified that a small subset of parameters disproportionately contributes '
     'to model brittleness.',
     'Several independent lines now point to the visual encoder as the more fragile component.'
     '~\\cite{schiappa2025robust} exposed MLLMs to visual adversarial perturbations;~\\cite{wang2025sea} '
     'traced fine-tuning to localized shifts in vision-side parameters; and~\\cite{zhu2026fi} showed that a '
     'small parameter subset carries a disproportionate share of model brittleness.', 1),
    ('Together, these findings independently validate the core mechanism behind our ODE prediction: $g_v$ '
     'is the dominant perturbation source.',
     'Read together these results motivate the visual term of our ODE, but---as Section~\\ref{sec:empirical} '
     'shows with a strict control---they do not establish that perturbing the visual encoder is what '
     'produces the alignment benefit.', 1),

    # line 23: the surveys paragraph (34-word run)
    ('~\\cite{gao2026uniformity} provided a unified theoretical treatment of uniformity and alignment '
     'objectives for multimodal representation learning. Comprehensive surveys~\\cite{vlm2026survey,'
     'chen2025vlmft,zhu2025connector} document the rapid evolution of VLM architectures and fine-tuning '
     'strategies.',
     '~\\cite{gao2026uniformity} gave a unified theoretical treatment of uniformity and alignment for '
     'multimodal representation learning, while the surveys~\\cite{vlm2026survey,chen2025vlmft,'
     'zhu2025connector} chart how VLM architectures and fine-tuning strategies have evolved.', 1),
]

cache = {F: io.open(F, encoding='utf-8').read()}
fail = []
for old, new, want in EDITS:
    got = cache[F].count(old)
    print('%-58s occurrences=%d' % (old[:56].replace('\n', ' '), got))
    if got != want:
        fail.append(old[:50])
        continue
    cache[F] = cache[F].replace(old, new)

if fail:
    print('ABORTED - nothing written (%d mismatches)' % len(fail))
    sys.exit(1)

io.open(F, 'w', encoding='utf-8', newline='').write(cache[F])
out = io.open(F, encoding='utf-8').read()
checks = [
    ('no "Visual Fragility" left', 'Visual Fragility' not in out),
    ('control mentioned', 'strict control' in out),
    ('Cone Effect reworded', 'earliest systematic account' in out),
    ('old opening gone', 'was first systematically characterized' not in out),
]
bad = 0
for name, ok in checks:
    print('  %-30s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

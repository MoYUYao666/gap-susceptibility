# -*- coding: utf-8 -*-
"""ap3 sync patch 2: the mechanism subsection and the gap/R@1 correlation block.

Sources for every replacement:
  n=204 rule + r values      outputs/analysis/dg_r1_reproducible.json (primary block)
  clustered bootstrap        same file, primary.cluster_bootstrap (12 clusters)
  GSNR 1.4x                  outputs/gsnr_results.json -> v_t_ratio 1.4111
                             (outputs/gsnr_results_pre_fix.json has the stale 1.4531)
  noise probe withdrawn      outputs/noise_fixed_aug.json (sigma=0 reproduces the baseline on
                             10/10 runs; sigma=0.1 vision 1.90+/-1.83 vs text 2.48+/-3.25, p=0.7718)
  effective rank on embeddings   compute_effective_rank(embeddings) in paper/scripts/noise_sensitivity.py
  legacy training convention     95.96% of parameters trainable (paper/sections/methodology.tex)
  zero-shot values + 0.8 claim   outputs/dtd_food101_zs_check.json (max |delta| = 0.74)
  ImageNet protocol              paper/sections/supplementary.tex footnote e (full 50k, single template)

Any count mismatch aborts the whole patch without writing.
"""
import io
import sys

F = 'paper_ap3/sections/04_mechanism.tex'
G = 'paper_ap3/sections/03b_special.tex'
I = 'paper_ap3/sections/01_intro.tex'

EDITS = [
    # ---- intro restatement of the correlation ----
    (I, 'identifies the modality gap as the state variable that predicts retrieval degradation ($r=-0.827$)',
     'identifies the modality gap magnitude as a state variable that co-varies with retrieval '
     'performance ($r=-0.714$ over a reproducible archive of 204 runs, where the centroid gap gives '
     '$r=-0.594$)', 1),

    # ---- 04_mechanism: the correlation subsection ----
    (F, 'A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance. '
        'Across the $n=81$ complete experiments spanning different methods, architectures, and datasets, '
        'DG achieves $r = -0.827$ with R@1, substantially outperforming CG ($r = -0.683$). '
        'Figure~\\ref{fig:corr} visualizes this relationship.',
     'A key statistical regularity is that the gap magnitude tracks retrieval performance. Across the '
     'reproducible archive of $n=204$ runs spanning different methods, architectures and datasets the '
     'Distribution Gap reaches $r = -0.714$ with R@1 and the Centroid Gap $r = -0.594$. The two gap '
     'measures are themselves correlated at $r = +0.945$, so we treat the association as a property of '
     'gap \\emph{magnitude} rather than as evidence that DG carries information the centroid gap lacks. '
     'Figure~\\ref{fig:corr} visualizes this relationship.', 1),

    (F, '\\caption{DG vs.\\ CG as retrieval predictors. DG achieves $r=-0.827$, substantially stronger than CG ($r=-0.683$).}',
     '\\caption{Gap magnitude vs.\\ R@1 over the reproducible archive ($n=204$). DG reaches $r=-0.714$ and '
     'CG $r=-0.594$; the two measures are correlated at $r=+0.945$, so neither is treated as strictly more '
     'informative than the other.}', 1),

    (F, 'Controlling for CG via partial correlation, DG retains $r = -0.807$ ($p < 0.001$), confirming that DG '
        'captures distributional shape information beyond first-order centroid shift (Table~\\ref{tab:corr}). '
        'In contrast, CG change (CG$\\Delta$) has no significant predictive power ($r = 0.012$, $p = 0.915$).',
     'Controlling for CG via partial correlation, DG retains $r = -0.581$ ($p < 0.001$), so part of the '
     'association survives the first-order centroid shift, but the shared variance is large '
     '(Table~\\ref{tab:corr}). Change measures are weak: DG$\\Delta$ gives $r = +0.134$ ($p = 0.055$) and '
     'CG$\\Delta$ $r = +0.190$ ($p = 0.007$), so the absolute magnitude rather than the direction of change '
     'is the informative quantity.', 1),

    (F, '\\caption{Pearson correlation between gap metrics and R@1 ($n=81$).}',
     '\\caption{Pearson correlation between gap metrics and R@1 over the reproducible archive ($n=204$: every '
     '\\texttt{outputs/**/results.json} with finite final CG, DG and R@1, one row per experiment directory).}', 1),

    (F, 'DG        & $\\mathbf{-0.827}$ & $\\mathbf{-0.807}$ & $<0.001$ \\\\\n'
        'CG        & $-0.683$ & --- & $<0.001$ \\\\\n'
        'CG$\\Delta$ & $+0.012$ & --- & $0.915$ (n.s.) \\\\',
     'DG        & $\\mathbf{-0.714}$ & $\\mathbf{-0.581}$ & $<0.001$ \\\\\n'
     'CG        & $-0.594$ & --- & $<0.001$ \\\\\n'
     'DG$\\leftrightarrow$CG & $+0.945$ & --- & $<0.001$ \\\\\n'
     'DG$\\Delta$ & $+0.134$ & --- & $0.055$ (n.s.) \\\\\n'
     'CG$\\Delta$ & $+0.190$ & --- & $0.007$ \\\\', 1),

    (F, 'To address potential concerns about non-independence among experiments sharing configurations, we '
        'performed a clustered bootstrap with the experiment directory (configuration family) as the cluster '
        'unit (98 experiments, 14 clusters, 10,000 resamples; the clustering is deliberately coarse, so it is '
        'conservative). The cluster-adjusted correlation is $r = -0.847$ (95\\% CI: $[-0.936, -0.709]$), with '
        '$0.04\\%$ of bootstrap samples yielding $r \\geq 0$. The DG--retrieval association is robust to '
        'within-configuration dependence; the cluster adjustment does not attenuate the correlation (naive '
        'Pearson over the same $n{=}98$ sample: $-0.857$; restricted subsets: $-0.815$ at $n{=}94$ and $-0.827$ '
        'at $n{=}81$).',
     'To address potential concerns about non-independence among experiments sharing configurations, we '
     'performed a clustered bootstrap with the first path component under \\texttt{outputs/} (the experiment '
     'family) as the cluster unit ($12$ clusters, 10{,}000 resamples). The cluster-adjusted correlation is '
     '$r = -0.738$ for DG (95\\% CI $[-0.889, -0.613]$), with none of the resamples yielding $r \\geq 0$, and '
     '$-0.608$ $[-0.777, -0.462]$ for CG. The gap--retrieval association is therefore robust to '
     'within-family dependence, and the adjustment does not separate the two measures.', 1),

    # ---- 04_mechanism: the mechanism subsection ----
    (F, 'Three independent lines of evidence support this interpretation (the interpretation is '
        'phenomenological: the evidence is consistent with it but does not deductively prove the mechanism, as '
        'noted below).',
     'Two lines of evidence are consistent with this interpretation, and a third that was originally reported '
     'here is withdrawn below; the interpretation is phenomenological, and the evidence is consistent with it '
     'rather than a deductive proof of the mechanism.', 1),

    (F, '\\textbf{Noise sensitivity.} We inject isotropic Gaussian noise into encoder parameters and measure '
        'retrieval degradation. Vision encoder noise causes $2.6\\times$ greater degradation than comparable '
        'text encoder noise, confirming that visual representations depend on more precisely tuned parameters.',
     '\\textbf{Noise sensitivity (withdrawn).} An earlier single evaluation of isotropic Gaussian noise in the '
     'encoder parameters suggested that vision-side noise degrades retrieval $2.6\\times$ more than text-side '
     'noise. Repeating the probe with the image set and the augmentation draw held fixed across conditions and '
     'with a $\\sigma=0$ control that reproduces the baseline exactly gives no stable ordering over five seeds '
     '($1.9 \\pm 1.8\\%$ for the vision encoder against $2.5 \\pm 3.3\\%$ for the text encoder at $\\sigma=0.1$, '
     'paired $p = 0.77$), so this line of evidence is not used.', 1),

    (F, 'The vision GSNR exceeds the text GSNR by $1.5\\times$',
     'The vision GSNR exceeds the text GSNR by $1.4\\times$', 1),

    (F, '\\textbf{Effective rank collapse.} We track the effective rank of the weight update matrix $\\Delta W$ '
        '(Frobenius norm $\\|\\Delta W\\|_F$) per encoder layer. Text-only training has zero vision-side weight '
        'perturbation by construction; joint-modality training produces substantial vision-side weight changes, '
        'with magnitude increasing with LoRA rank. This links directly to the ODE prediction:',
     '\\textbf{Effective rank of the embeddings.} We track the effective rank $\\exp(-\\sum_i p_i \\log p_i)$ of '
     'the per-layer image embeddings, where $p_i$ are the normalised singular values of the mean-pooled token '
     'representations. In the text-only runs the vision-side effective rank falls ($9.43$ to $6.16$--$7.02$ '
     'across three of four runs), but those runs were trained under a convention in which $95.96\\%$ of the '
     "model's parameters remained trainable (only the 24 replaced $q/v$ projections were frozen), so the "
     'reduction is not by itself evidence that adapters on the text side perturbed the visual space. '
     'Joint-modality training produces substantially larger vision-side weight changes, with magnitude '
     'increasing with LoRA rank. This links directly to the ODE prediction:', 1),

    # ---- 04_mechanism: zero-shot subsection ----
    (F, 'On ImageNet, text-only preserves 58.66\\% accuracy',
     'On ImageNet (full 50{,}000-image validation set, single template), text-only preserves 58.66\\% accuracy', 1),

    (F, 'the text-only and both-position variants stay within $0.9$ percentage points of the frozen baseline (the ImageNet collapse',
     'the text-only and both-position variants stay within $0.8$ percentage points of the frozen baseline (the ImageNet collapse', 1),

    (F, '\\caption{Zero-shot classification on DTD and Food101 after Flickr30k fine-tuning. The text-only and '
        'both-position variants stay within 0.9 percentage points of the frozen baseline',
     '\\caption{Zero-shot classification on DTD and Food101 after Flickr30k fine-tuning. The text-only and '
     'both-position variants stay within 0.8 percentage points of the frozen baseline', 1),

    # ---- 03b_special restatement ----
    (G, 'The empirical finding that DG predicts R@1 at $r=-0.827$ (partial $r=-0.807$ controlling for CG) follows '
        'naturally from the ODE:',
     'The empirical regularity that the gap magnitude co-varies with R@1---DG at $r=-0.714$, CG at $r=-0.594$, '
     'partial $r=-0.581$ controlling for CG---follows naturally from the ODE:', 1),
]

cache, failures = {}, []
for path, old, new, want in EDITS:
    if path not in cache:
        cache[path] = io.open(path, encoding='utf-8').read()
    got = cache[path].count(old)
    if got != want:
        failures.append('%s: expected %d, found %d for %r' % (path, want, got, old[:70]))
        continue
    cache[path] = cache[path].replace(old, new)

if failures:
    print('ABORTED - nothing written:')
    for f in failures:
        print('  - ' + f)
    sys.exit(1)

for path, text in cache.items():
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)
    print('wrote %s' % path)

joined = '\n'.join(cache.values())
checks = [
    ('n=204 present', 'n=204' in joined or 'n{=}204' in joined or '$n=204$' in joined),
    ('-0.714 present', '-0.714' in joined),
    ('-0.594 present', '-0.594' in joined),
    ('-0.581 present', '-0.581' in joined),
    ('+0.945 present', '+0.945' in joined),
    ('12 clusters present', '12$ clusters' in joined or '12} clusters' in joined),
    ('-0.738 present', '-0.738' in joined),
    ('1.4x GSNR present', '1.4\\times' in joined),
    ('0.8 points claim present', 'within $0.8$ percentage points' in joined),
    ('no -0.827 left', '-0.827' not in joined),
    ('no -0.807 left', '-0.807' not in joined),
    ('no -0.683 left', '-0.683' not in joined),
    ('no n=81 left', 'n=81' not in joined),
    ('no 2.6x claim left', 'causes $2.6\\times$' not in joined),
    ('no 1.5x GSNR left', 'text GSNR by $1.5\\times$' not in joined),
    ('no zero-perturbation claim left', 'zero vision-side weight perturbation by construction' not in joined),
    ('no weight-matrix effective rank left', 'weight update matrix $\\Delta W$' not in joined),
    ('no 0.9 points left', 'within $0.9$ percentage points' not in joined and 'within 0.9 percentage points' not in joined),
]
bad = 0
for name, ok in checks:
    print('  %-38s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

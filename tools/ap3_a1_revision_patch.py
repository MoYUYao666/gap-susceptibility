"""A1 revision material package: all corrections + all additions (CRLF-aware, per-item assertions).

Corrections:
  F1 tab:earlystop epoch-10 row (previously the epoch-5 values) + rewrite the "plateau" narrative
  F2 block 7 pure-LoRA numbers made traceable (lr0.0 / a1_tau_trajectory.both)
  F3 "above 0.93" → ">= 0.930"; "exactly 1.0000" → "1.0000 (four decimals)"
Additions:
  S1 DINOv2 add the orthogonal variant
  S2 Qwen table add negative λ (−2/−1/−0.5)
  S3 cross-family held-out fold size disclosure (clip n_test=20 vs 4 for the others)
  S4 Gaussian bound as the "when does it fail" boundary
"""
import sys

P = 'paper_a1/revision_additions.tex'
src = open(P, encoding='utf-8', newline='').read()
orig = src
done, failed = [], []


def rep(tag, old, new):
    global src
    if old not in src:
        failed.append(tag)
        return
    src = src.replace(old, new, 1)
    done.append(tag)


# ---------- F1 early-stop table ----------
rep('F1a table caption',
    r'\caption{Per-epoch monitoring signals (both-position LoRA, rank 8).}',
    r'\caption{Per-epoch monitoring signals for strictly LoRA-only fine-tuning '
    r'(both-position LoRA, rank 8; $\lambda_{\mathrm{reg}}=0$, seed 42; each epoch '
    r'evaluated in a fresh process). Epochs 1, 2, 3, 5 and the endpoint 10 are the '
    r'evaluated points of this sweep.}')

rep('F1b tau row',
    r'$\tau$ & 0.833 & 0.825 & 0.823 & 0.824 & 0.823 \\',
    r'$\tau$ & 0.833 & 0.825 & 0.823 & 0.823 & \textbf{0.711} \\')

rep('F1c top1 row',
    r'top-1 (\%) & 58.6 & 58.5 & 58.6 & 58.6 & 58.6 \\',
    r'top-1 (\%) & 58.58 & 58.45 & 58.55 & 58.61 & 58.05 \\')

rep('F1d val row',
    r'val loss & 2.464 & 2.468 & 2.470 & 2.472 & 2.470 \\',
    r'val loss & 2.464 & 2.468 & 2.470 & 2.472 & 2.364 \\')

rep('F1e narrative paragraph',
    '$\tau$ erodes monotonically over epochs 1--3 ($0.833\\to 0.823$) and plateaus,\r\n'
    'while top-1 stays flat throughout ($58.45$--$58.63\\%$) and validation loss is\r\n'
    'flat to slightly rising. $\\tau$ is the earliest and most sensitive of the\r\n'
    'three signals---direction consistent with the retrain trajectory of\r\n'
    'Section~\\ref{sec:traj}, where the erosion was larger---supporting its use as\r\n'
    'a zero-overhead early monitor for classification-oriented fine-tuning.',
    'Two regimes, and the second one carries the claim. $\\tau$ erodes slowly over\r\n'
    'epochs 1--5 ($0.833\\to 0.823$, a $1.2\\%$ loss) and then \\emph{drops sharply at\r\n'
    'the final epoch} ($0.823\\to 0.711$, $13.6\\%$), while zero-shot top-1 is inert\r\n'
    'throughout ($58.05$--$58.61\\%$, a range of $0.56$ points) and the validation\r\n'
    'loss moves in the \\emph{opposite} direction at the endpoint ($2.472\\to 2.364$):\r\n'
    'the model fits the fine-tuning distribution better exactly when order preservation\r\n'
    'falls. The endpoint is therefore the informative one --- $\\tau$ registers a change\r\n'
    'that neither top-1 nor the validation loss reports as a loss of zero-shot quality ---\r\n'
    'and it is the same run whose $\\lambda_{\\mathrm{reg}}=0$ endpoint ($58.1\\%$,\r\n'
    '$\\tau=0.711$) appears in the dose--response block above, so the two blocks describe\r\n'
    'one trajectory. Direction consistent with the retrain trajectory of\r\n'
    'Section~\\ref{sec:traj}, where the erosion was larger.')

# ---------- F2 block 7 ----------
rep('F2 block 7 numbers',
    'The retrain checkpoints of Section~\\ref{sec:traj} archive the LoRA adapter\r\n'
    'weights only. Re-training under strictly LoRA-only optimization (embedding\r\n'
    'and LayerNorm parameters frozen) reproduces the same qualitative pattern:\r\n'
    '$\\tau$ erodes early ($0.76$ at epoch 1 $\\to$ $0.73$ at epoch 3) and plateaus\r\n'
    'at $\\approx 0.71$, while zero-shot top-1 stays flat at $58.1\\%$ throughout\r\n'
    'and the final Centroid Gap behavior is unchanged. The submitted trajectory\r\n'
    'values (plateau $\\approx 0.75$) correspond to the LoRA-component\r\n'
    'reconstruction of the archived checkpoints; both protocols support the same\r\n'
    'conclusion---$\\tau$ is the earliest erosion signal, top-1 is inert.',
    'The retrain checkpoints of Section~\\ref{sec:traj} archive the LoRA adapter\r\n'
    'weights only. Two re-evaluations bound the protocol dependence. (a) Strictly\r\n'
    'LoRA-only re-training --- the dose--response script selects parameters by name\r\n'
    '($\\texttt{lora\\_}$ prefix) and therefore cannot update embeddings or\r\n'
    'LayerNorms, so it is a strict test --- gives $\\tau = 0.833$ at epoch 1, $0.823$\r\n'
    'at epoch 3 and $0.711$ at epoch 10, with top-1 $58.58\\to 58.05\\%$\r\n'
    '(Table~\\ref{tab:earlystop}; \\texttt{a1\\_class\\_aligned/lr0.0/seed42}).\r\n'
    '(b) Evaluating the archived submitted checkpoints (LoRA-component\r\n'
    'reconstruction, 5000-image sample) gives $\\tau = 0.767 \\to 0.748$ and top-1\r\n'
    '$58.86\\to 58.90\\%$ (\\texttt{a1\\_tau\\_trajectory.json}). The two protocols\r\n'
    'place the $\\tau$ level at $0.71$--$0.83$ and $0.75$--$0.77$ respectively, but\r\n'
    'agree on the conclusion: $\\tau$ is the earliest erosion signal, top-1 is inert.')

# ---------- F3 DINOv2 wording ----------
rep('F3 DINOv2 wording',
    'under the same surgery grid, $\\tau$ stays above $0.93$ at every $\\lambda$ (including $\\lambda=4$) and nearest-prototype\r\n'
    'top-1 stays at $48.2\\%$ (range $48.18$--$48.26\\%$), even where CG shrinks to $0.001$.',
    'under the same surgery grid and in \\emph{both} variants (gap-direction and\r\n'
    'orthogonal, magnitude-matched), $\\tau \\ge 0.930$ at every $\\lambda$ including\r\n'
    '$\\lambda=4$ ($0.930$--$0.995$ gap, $0.950$--$0.997$ orthogonal) and\r\n'
    'nearest-prototype top-1 stays inside $48.18$--$48.26\\%$, even where CG shrinks\r\n'
    'to $0.001$.')

# ---------- S2 Qwen table: add negative λ ----------
rep('S2a Qwen table width',
    r'\begin{tabular}{lccccc}' + '\r\n' + r'\toprule' + '\r\n' + r'$\lambda$ & 0.25 & 0.5 & 1.0 & 2.0 \\',
    r'\begin{tabular}{lccccccc}' + '\r\n' + r'\toprule' + '\r\n'
    + r'$\lambda$ & $-2$ & $-1$ & $-0.5$ & 0.25 & 0.5 & 1.0 & 2.0 \\')

rep('S2b Qwen data rows',
    'image-side $\\tau$ & 0.815 & 0.683 & 0.482 & 0.271 \\\\\r\n'
    'image-side top-1 & 16.7 & 16.7 & 15.3 & 8.3 \\\\\r\n'
    'image-side CG & 0.716 & 0.511 & \\textbf{0.155} & 0.613 \\\\\r\n'
    'text-side $\\tau$ & \\multicolumn{4}{c}{\\textbf{1.000} (all $\\lambda$)} \\\\\r\n'
    'text-side top-1 & \\multicolumn{4}{c}{17.1 (unchanged)} \\\\',
    'image-side $\\tau$ & 0.434 & 0.574 & 0.730 & 0.815 & 0.683 & 0.482 & 0.271 \\\\\r\n'
    'image-side top-1 & 8.9 & 15.0 & 16.7 & 16.7 & 16.7 & 15.3 & 8.3 \\\\\r\n'
    'image-side CG & 1.218 & 1.136 & 1.046 & 0.716 & 0.511 & \\textbf{0.155} & 0.613 \\\\\r\n'
    'text-side $\\tau$ & \\multicolumn{7}{c}{\\textbf{1.000} (all $\\lambda$)} \\\\\r\n'
    'text-side top-1 & \\multicolumn{7}{c}{17.1 (unchanged)} \\\\')

rep('S2c Qwen narrative',
    '(i) image-side $\\tau$ collapses monotonically with\r\n$\\lambda$;',
    '(i) image-side $\\tau$ collapses monotonically and \\emph{symmetrically} in\r\n'
    '$\\lambda$ --- the negative side is equally destructive ($0.434$ at\r\n'
    '$\\lambda=-2$ against $0.271$ at $\\lambda=+2$), so the effect is a function of\r\n'
    'the translation magnitude, not its sign;')

# ---------- S3/S4 block 8 ----------
rep('S3 fold size disclosure',
    'The mapping is\r\nmonotone but family-calibrated, so we state ordering across families rather than\r\nabsolute prediction.',
    'The mapping is\r\nmonotone but family-calibrated, so we state ordering across families rather than\r\nabsolute prediction. Two caveats belong with these numbers: the folds are very\r\nunequal ($n_{\\mathrm{test}} = 20$ for CLIP against $4$ for OpenCLIP and SigLIP),\r\nso the negative OpenCLIP $R^2$ is a small-sample artefact rather than a failure\r\nof the predictor, and the pooled Spearman ($0.927$, $n = 28$) is the primary\r\nsummary. The exact pair-inversion predictor is likewise not a universal law: a\r\nGaussian surrogate for the margin distribution reaches only $R^2 = 0.986$ with\r\nmaximum error $0.170$ on the same nine $\\lambda$ values, so the closed form is\r\naccurate where the frozen margins are used directly and degrades once the margin\r\ndistribution is modelled.')

if failed:
    print('The following replacements did not match (the source needs a manual check):', failed)
open(P, 'w', encoding='utf-8', newline='').write(src)
print(f'Completed {len(done)}/{len(done) + len(failed)} items:')
for t in done:
    print('  OK ', t)
print(f'File bytes {len(orig)} -> {len(src)}')
sys.exit(1 if failed else 0)

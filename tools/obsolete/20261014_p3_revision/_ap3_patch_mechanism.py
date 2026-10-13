# -*- coding: utf-8 -*-
"""ap3 sync patch 8: the mechanism subsection stops asserting a refuted explanation.

The operator asked for the factually correct option.  The correct position is that printed in the
companion work after its strict control: text-only adaptation reduces the gap even when the visual
encoder provably does not change, so the benefit comes from *where the adapters sit*, not from
perturbing the visual space, and the "visual fragility" reading cannot be the explanation even
though the gradient-pressure probes point the way they do.

Numbers (outputs/analysis/strict_control_summary.json):
  strict text-only   5 seeds, 196,608 trainable parameters (0.13% of 151,277,313),
                     CG delta -0.04650 +/- 0.00270, R@1 0.62380 +/- 0.00492,
                     vision_nonzero_tensors 0 of 199, vision rank change exactly 0
  legacy text-only   single run, 145,170,177 trainable (vision encoder included), CG delta -0.06354

Edits: retitle the subsection, replace its opening claim, add the control paragraph, and rewrite the
closing sentence so the probes are reported as evidence about gradient pressure rather than as the
explanation of the text-only benefit.
"""
import io
import sys

F = 'paper_ap3/sections/04_mechanism.tex'

EDITS = [
    ('\\subsection{Visual Fragility Interpretation}',
     '\\subsection{Mechanism Probes and a Strict Control}', 1),

    ('Why does text-only preserve alignment? We propose the \\textbf{Visual Fragility Interpretation}: '
     'visual embedding spaces are more sensitive to parameter perturbation than text spaces. Two lines '
     'of evidence are consistent with this interpretation, and a third that was originally reported '
     'here is withdrawn below; the interpretation is phenomenological, and the evidence is consistent '
     'with it rather than a deductive proof of the mechanism.',
     'Why does text-only preserve alignment? One candidate account is that visual embedding spaces are '
     'more sensitive to parameter perturbation than text spaces. Two probes below are consistent with '
     'a larger vision-side gradient contribution, a third is withdrawn, and a strict control then '
     'separates the two readings: the alignment benefit does not come from perturbing the visual '
     'space---it comes from \\emph{where the adapters sit}.', 1),

    ('We emphasize that Visual Fragility is a phenomenological interpretation supported by converging '
     'evidence, not a deductively proven mechanism. Section~\\ref{sec:theory} provides the formal '
     'framework that explains \\emph{why} visual fragility emerges from gradient geometry.',
     '\\textbf{Strict control.} The archived text-only runs trained $145{,}170{,}177$ parameters, the '
     'vision encoder included, so they cannot separate adapter placement from vision-side updates. A '
     'control in which every non-adapter parameter is frozen removes the confound: it trains '
     '$196{,}608$ parameters ($0.13\\%$ of the model), leaves all $199$ vision-encoder tensors '
     'bit-identical (the vision-side effective-rank change is exactly zero), and still reduces the gap '
     '(CG$\\Delta = -0.0465 \\pm 0.0027$, R@1 $0.6238 \\pm 0.0049$ over five seeds). Vision-side '
     'updates are therefore inert with respect to this outcome: the text-only benefit is governed by '
     'adapter placement, and the probes above are evidence about where the alignment-relevant gradient '
     'pressure sits rather than an explanation of the benefit itself. Section~\\ref{sec:theory} '
     'derives why the vision-side coupling dominates the perturbation force under either reading.', 1),
]

cache = {F: io.open(F, encoding='utf-8').read()}
fail = []
for old, new, want in EDITS:
    got = cache[F].count(old)
    print('%-46s occurrences=%d' % (old[:44].replace('\n', ' '), got))
    if got != want:
        fail.append(old[:60])
        continue
    cache[F] = cache[F].replace(old, new)

if fail:
    print('ABORTED - nothing written: %s' % fail)
    sys.exit(1)

io.open(F, 'w', encoding='utf-8', newline='').write(cache[F])
print('wrote %s' % F)

out = io.open(F, encoding='utf-8').read()
checks = [
    ('subsection retitled', 'Mechanism Probes and a Strict Control' in out),
    ('old title gone', 'Visual Fragility Interpretation' not in out),
    ('control paragraph present', '\\textbf{Strict control.}' in out),
    ('strict numbers present', '-0.0465 \\pm 0.0027' in out and '196{,}608' in out),
    ('zero vision tensors stated', 'all $199$ vision-encoder tensors' in out),
    ('no explanation claim left', 'We propose the \\textbf{Visual Fragility}' not in out),
    ('gradient-pressure framing', 'gradient\npressure sits' in out or 'gradient pressure sits' in out),
]
bad = 0
for name, ok in checks:
    print('  %-36s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

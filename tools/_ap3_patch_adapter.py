# -*- coding: utf-8 -*-
"""ap3 sync patch 4: the Adapter claims, and the caption that describes a figure which does not exist.

Source of truth: outputs/analysis/adapter_common_baseline.json
  frozen_reference_cg = 0.8184 (mean of three same-protocol frozen evaluations)
  adapter_d16_text  +0.2368 | adapter_d32_text +0.1029 | adapter_d64_text +0.0636   (vs frozen)
  adapter_d16_both  +0.5003 | adapter_d16_vis  +0.1806 | adapter_d4_text +0.2589 | adapter_d8_text +0.2620
  group means: text-only n=5 +0.1848, all seven +0.2293
  the published convention (final minus each run's own post-injection initial) gave d64 = -0.2167,
  which is the "-0.217" the manuscript quotes at 05_dynamics.tex:111.

Also verified against paper/sections/experiments.tex:126 and :138, which keep the ordering claim
("while LoRA favors lower rank, Adapter favors larger bottleneck dimension") while stating that no
Adapter configuration reduces the gap against the frozen model -- the two papers must not disagree.

Figure check: paper_ap3/figures/fig_crossmethod.png plots three LoRA ablation panels (rank, alpha,
target modules) and contains no Adapter data at all, so its caption's "LoRA and Adapter ...
opposite rank-dimension scaling" describes a figure that does not exist.
"""
import io
import sys

F = 'paper_ap3/sections/04_mechanism.tex'
D = 'paper_ap3/sections/05_dynamics.tex'

EDITS = [
    (F, 'Figure~\\ref{fig:crossmethod} compares PEFT methods. Text-only LoRA and Adapter both preserve '
        'alignment, but with opposite rank scaling: lower LoRA rank preserves better, while larger Adapter '
        'bottleneck dimension reduces gap more effectively.',
     'Figure~\\ref{fig:crossmethod} collects the LoRA ablations over rank, scaling factor and target modules, '
     'all measured against the frozen model. Text-only LoRA and Adapter both protect alignment relative to '
     'joint training, but with opposite rank scaling: for LoRA a lower rank preserves better, while for '
     'Adapter a \\emph{larger} bottleneck gives the smaller increase ($d$=16 $+0.237$, $d$=32 $+0.103$, '
     '$d$=64 $+0.064$ against the frozen baseline). No Adapter configuration brings the gap below the frozen '
     'value---these are increases---because a randomly initialised bottleneck enlarges the geometry on '
     'insertion (CG $1.08$--$1.36$ against the frozen $0.818$), which is the state the earlier convention '
     'measured each run against.', 1),

    (F, '\\caption{Cross-method comparison. LoRA and Adapter both benefit from text-only training, but exhibit '
        'opposite rank-dimension scaling.}',
     '\\caption{LoRA ablations, all measured against the frozen model (CG$\\Delta$; lower is better). Ranks '
     'below 16 leave the gap at or below its frozen value while ranks 32 and 64 enlarge it, a larger scaling '
     'factor reduces it monotonically, and adding key/value/output projections (QVKO) is more protective than '
     'query alone. The Adapter runs are measured on a different baseline and are reported in the text.}', 1),

    (F, '(2) \\textbf{Lower LoRA rank preserves alignment better}---while Adapter exhibits the opposite trend '
        '(larger bottleneck dimension reduces gap more effectively);',
     '(2) \\textbf{Lower LoRA rank preserves alignment better}---while for Adapter a larger bottleneck '
     'dimension gives the smaller increase ($d$=16 $+0.237$, $d$=32 $+0.103$, $d$=64 $+0.064$ against the '
     'frozen model, and no Adapter configuration reduces the gap);', 1),

    (D, 'whereas on Adapter the text-only variant is the protective one (CG$\\Delta = -0.217$ at $d=64$), '
        'consistent with $g_v = 0$ removing the dominant perturbation source when the visual pathway carries '
        'the update.',
     'whereas for Adapter the text-only variant at $d=64$ gives the smallest increase of the seven archived '
     'runs (CG$\\Delta = +0.064$ against the frozen model; the earlier $-0.217$ measured the same run against '
     'its own post-injection state), consistent with $g_v = 0$ removing the dominant perturbation source when '
     'the visual pathway carries the update.', 1),
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
    ('d=16 +0.237 present', '+0.237' in joined),
    ('d=32 +0.103 present', '+0.103' in joined),
    ('d=64 +0.064 present', '+0.064' in joined),
    ('-0.217 only inside the withdrawal note', 'the earlier $-0.217$ measured' in joined
     and 'CG$\\Delta = -0.217$' not in joined),
    ('no "reduces gap more effectively"', 'reduces gap more effectively' not in joined),
    ('no "compares PEFT methods"', 'compares PEFT methods' not in joined),
    ('caption no longer claims a cross-method figure',
     'Cross-method comparison. LoRA and Adapter both benefit' not in joined),
    ('frozen baseline named in the Adapter sentence', 'against the frozen baseline' in joined),
    ('no-Adapter-reduces-the-gap stated', 'no Adapter configuration reduces the gap' in joined),
]
bad = 0
for name, ok in checks:
    print('  %-44s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

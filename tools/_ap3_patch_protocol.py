# -*- coding: utf-8 -*-
"""ap3 sync patch 6: the training-protocol sentence moves to the archived convention.

Source: paper/sections/methodology.tex:20 states the corrected convention -- batch 128 for the
five-seed runs, the strict control and the Adapter experiments, and 64 for the earlier single-run
comparisons; the archived step counts record the difference (single Flickr LoRA runs: 630 steps =
64 x ~4,000 train images; five-seed and Adapter runs: 320 steps = 128 x ~2,000).  ap3 still carries
the blanket claim "All experiments use batch size 128", which contradicts it.

ap3 has no strict-control experiment, so that arm is not named here.
"""
import io
import sys

F = 'paper_ap3/sections/04_mechanism.tex'

OLD = ('All experiments use batch size 128, 10 epochs, AdamW (lr $10^{-4}$), on a single NVIDIA '
       'RTX 4060 GPU.')
NEW = ('All experiments run for 10 epochs with AdamW at $10^{-4}$ on a single NVIDIA RTX 4060 GPU. '
       'The batch size is 128 for the five-seed runs and the Adapter experiments, and 64 for the '
       'earlier single-run comparisons reported in Table~\\ref{tab:position}; the archived step '
       'counts record the difference.')

src = io.open(F, encoding='utf-8').read()
n = src.count(OLD)
print('%s: occurrences=%d' % (F, n))
if n != 1:
    print('ABORTED - nothing written (expected exactly one occurrence)')
    sys.exit(1)
io.open(F, 'w', encoding='utf-8', newline='').write(src.replace(OLD, NEW))
print('wrote %s' % F)

out = io.open(F, encoding='utf-8').read()
checks = [
    ('batch-128 blanket claim gone', 'All experiments use batch size 128' not in out),
    ('split convention present', 'batch size is 128 for the five-seed runs and the Adapter experiments' in out),
    ('step counts referenced', 'the archived step counts record the difference' in out),
    ('no strict-control mention (not an ap3 experiment)', 'strict control' not in out.lower()),
]
bad = 0
for name, ok in checks:
    print('  %-52s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

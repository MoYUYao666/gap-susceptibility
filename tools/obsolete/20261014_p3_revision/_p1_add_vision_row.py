# -*- coding: utf-8 -*-
"""Add the vision-only arm to the strict-freeze table and extend the surrounding sentence.

Values from outputs/analysis/strict_control_summary.json (5 seeds each, same protocol):
  text-only  CG delta -0.0465 +/- 0.0027   R@1 0.6238   196,608 trainable   vision rank change 0.0000
  both       CG delta -0.0258 +/- 0.0031   R@1 0.6932   491,520             vision rank change -0.0421
  vision-only CG delta +0.0106 +/- 0.0039  R@1 0.6800   294,912             text rank change 0.0000

The three-arm ordering is the informative part: gap reduction is largest for text-only, smaller for
the joint arm, and absent for vision-only, while retrieval orders differently -- so the two metrics
move in opposite directions inside this control, which the text now states.
"""
import io
import sys

F = 'paper/sections/strict_control.tex'

EDITS = [
    ('Both & 5 & 491,520 & $-0.026 \\pm 0.003$ & 0.693 & 0/199 \\\\\n',
     'Both & 5 & 491,520 & $-0.026 \\pm 0.003$ & 0.693 & 0/199 \\\\\n'
     'Vision-only & 5 & 294,912 & $+0.011 \\pm 0.004$ & 0.680 & 0/199 \\\\\n', 1),
    ('Note also\nthat the two arms differ in retrieval in the opposite direction to their gap reduction: text-only\n'
     'leaves the smaller gap and retrieves worse ($0.624$) than the joint arm ($0.693$), so gap\n'
     'magnitude and retrieval quality do not move together within this control.',
     'The three arms order in opposite directions on the two metrics: gap reduction is largest for\n'
     'text-only ($-0.047$), smaller for the joint arm ($-0.026$), and absent for vision-only\n'
     '($+0.011$), while retrieval is $0.624$, $0.693$ and $0.680$ respectively. Gap magnitude and\n'
     'retrieval quality therefore do not move together inside this control, and the retrieval ordering\n'
     'is not explained by where the adapters sit either.', 1),
]

cache = {F: io.open(F, encoding='utf-8').read()}
fail = []
for old, new, want in EDITS:
    got = cache[F].count(old)
    print('%-52s occurrences=%d' % (old[:50].replace('\n', ' '), got))
    if got != want:
        fail.append(old[:44].replace('\n', ' '))
        continue
    cache[F] = cache[F].replace(old, new)

if fail:
    print('ABORTED - nothing written: %s' % fail)
    sys.exit(1)

io.open(F, 'w', encoding='utf-8', newline='').write(cache[F])
out = io.open(F, encoding='utf-8').read()
checks = [
    ('vision-only row present', 'Vision-only & 5 & 294,912' in out),
    ('three arms described', 'The three arms order in opposite directions' in out),
    ('old two-arm sentence gone', 'the two arms differ in retrieval' not in out),
    ('row count in table', out.count(' & 5 & ') == 3),
]
bad = 0
for name, ok in checks:
    print('  %-32s %s' % (name, 'PASS' if ok else 'FAIL'))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)

# -*- coding: utf-8 -*-
"""Two single-line corrections, each with a count assertion.

1. paper/sections/supplementary.tex footnote b: the both-modality final loss is 0.6127 in the
   corrected GSNR run (outputs/gsnr_results.json), not the 0.5615 of the pre-fix archive
   (outputs/gsnr_results_pre_fix.json); the text-only loss is 4.1565 -> 4.16.  Figure 11's own
   caption already says "4.16 vs. 0.61", so the footnote was the inconsistent one.
2. paper_ap3/refs.bib xu2026vlreasoning: the verified title ends "in reasoning" (external evidence
   recorded in docs/P1_REVIEW_CITATIONS.md; the P1 entry carries the full title).
"""
import io
import sys

EDITS = [
    ('paper/sections/supplementary.tex',
     r'text-only converges to a higher final loss (4.15 vs.\ 0.56 for both-modality)',
     r'text-only converges to a higher final loss (4.16 vs.\ 0.61 for both-modality)'),
    ('paper_ap3/refs.bib',
     'title     = {Do vision-language models truly perform vision reasoning? {A} rigorous study of the modality gap},',
     'title     = {Do vision-language models truly perform vision reasoning? {A} rigorous study of the modality gap in reasoning},'),
]

fail = []
cache = {}
for p, old, new in EDITS:
    if p not in cache:
        cache[p] = io.open(p, encoding='utf-8').read()
    n = cache[p].count(old)
    print('%-44s occurrences=%d' % (p, n))
    if n != 1:
        fail.append('%s (%d occurrences)' % (p, n))
    else:
        cache[p] = cache[p].replace(old, new)

if fail:
    print('ABORTED, nothing written: %s' % ', '.join(fail))
    sys.exit(1)

for p, t in cache.items():
    io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print('wrote %s' % p)

ok = (('4.16 vs.\\ 0.61' in cache['paper/sections/supplementary.tex'])
      and ('4.15 vs.\\ 0.56' not in cache['paper/sections/supplementary.tex'])
      and ('modality gap in reasoning},' in cache['paper_ap3/refs.bib']))
print('post-conditions: %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)

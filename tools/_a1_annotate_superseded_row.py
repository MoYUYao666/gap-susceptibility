# -*- coding: utf-8 -*-
"""Annotate the superseded decision row in docs/A1_VENUE_DECISION.md.

The section-1 table still records "A1 目标刊 = Image and Vision Computing", which was the
decision at the time; sections 6 and 8 later excluded IVC and settled on Neurocomputing.
The row is left as history but is marked as superseded, so the three places cannot be read
as contradicting each other."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

with io.open(DOC, encoding='utf-8') as f:
    lines = f.read().split('\n')

hits = [i for i, l in enumerate(lines) if l.startswith('| A1 目标刊 |')]
if len(hits) != 1:
    print('ABORT: expected 1 target-journal row, found %d' % len(hits))
    sys.exit(1)

i = hits[0]
lines[i] = ('| A1 目标刊 | ~~Image and Vision Computing（Elsevier，中科院 3 区）~~ '
            '**已被取代 → Neurocomputing（Elsevier，2 区）**；排除 IVC 的原因见第六节，'
            '最终决定见第八节 |')

with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

print('OK: row %d annotated as superseded' % (i + 1))
print('   now reads: ' + lines[i])

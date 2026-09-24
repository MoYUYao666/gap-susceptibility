# -*- coding: utf-8 -*-
"""Fix a stale trap in the prepared-wording table of docs/A1_VENUE_DECISION.md.

Section 5 pre-writes the three edits that A23 will need once A1 has actually been
submitted.  Those were written while A1 was still aimed at Image and Vision Computing;
A1 is now aimed at Neurocomputing (IVC was ruled out by its 4500-7500 word limit).  If a
later session applied the table verbatim it would name the wrong journal in A23.

Only the three prepared-replacement cells are touched; the surrounding prose that
discusses IVC and why it was rejected must keep saying IVC."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

PAIRS = [
    ('the revised manuscript has been submitted to \\emph{Image and Vision Computing})',
     'the revised manuscript has been submitted to \\emph{Neurocomputing})',
     'cover_letter.tex replacement'),
    ('the revised manuscript has been submitted to Image and Vision Computing.',
     'the revised manuscript has been submitted to Neurocomputing.',
     'main.tex wan2026a replacement'),
    ('（已收到决定）；修订版已投 Image and Vision Computing.',
     '（已收到决定）；修订版已投 Neurocomputing.',
     'main_zh.tex wan2026a replacement'),
]

with io.open(DOC, encoding='utf-8') as f:
    text = f.read()

log = []
for old, new, label in PAIRS:
    n = text.count(old)
    if n != 1:
        print('ABORT: %s -- expected 1 occurrence, found %d' % (label, n))
        sys.exit(1)
    text = text.replace(old, new)
    log.append('  OK  ' + label)

# the IVC discussion itself must survive
if 'IVC 被排除' not in text or '4500-7500' not in text:
    print('ABORT: the IVC exclusion section appears to have been damaged')
    sys.exit(1)
log.append('  OK  the IVC exclusion record is intact')

if 'submitted to Image and Vision Computing' in text or '已投 Image and Vision Computing' in text:
    print('ABORT: a stale IVC submission wording survives')
    sys.exit(1)
log.append('  OK  verified: no stale IVC submission wording remains')

with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('applied:')
for line in log:
    print(line)

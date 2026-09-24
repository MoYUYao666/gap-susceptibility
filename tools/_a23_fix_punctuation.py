# -*- coding: utf-8 -*-
"""Repair the punctuation my companion-status replacement broke.

The replaced span began mid-sentence at "(decision received); ...", so removing it left
"Pattern Recognition Letters The revised manuscript ..." with no sentence break.  The cover
letter is unaffected because its replacement kept the parenthetical intact."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXES = [
    ('paper_a2/main.tex',
     'previously submitted to Pattern Recognition Letters The revised manuscript',
     'previously submitted to Pattern Recognition Letters. The revised manuscript',
     'main.tex: sentence break restored'),
    ('paper_a2/main_zh.tex',
     '曾投 Pattern Recognition Letters修订版已投',
     '曾投 Pattern Recognition Letters。修订版已投',
     'main_zh.tex: 句号恢复'),
]

for rel, old, new, label in FIXES:
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    with io.open(p, encoding='utf-8') as f:
        t = f.read()
    n = t.count(old)
    if n != 1:
        print('ABORT %s: expected 1 occurrence, found %d' % (rel, n))
        sys.exit(1)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t.replace(old, new))
    print('  OK  %s' % label)

print('')
print('=== the three disclosures as they now read, in full ===')
for rel in ('paper_a2/cover_letter.tex', 'paper_a2/main.tex', 'paper_a2/main_zh.tex'):
    with io.open(os.path.join(ROOT, rel.replace('/', os.sep)), encoding='utf-8') as f:
        t = f.read()
    i = t.find('NEUCOM')
    while i != -1:
        start = max(0, i - 240)
        print('  %s' % rel)
        print('    ...' + ' '.join(t[start:i + 80].split()) + '...')
        i = t.find('NEUCOM', i + 1)

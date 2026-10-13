# -*- coding: utf-8 -*-
"""A23 also claims the project repository is public, which it is not.

A1's version of this claim was reverted earlier, but A23 carried its own wording, written
before the repository status was known -- the manuscript says the code and result JSONs are
"committed to the public repository companion to this paper", and the cover letter names
the URL and calls it "the public repository".  Both would be untrue statements in a
submitted manuscript, so both are corrected, together with the Chinese mirror.

Each replacement is attempted only where its target text occurs exactly once; every
occurrence of the offending phrase is printed with context first, so a mismatch is visible
rather than silently skipped."""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['paper_a2/main.tex', 'paper_a2/cover_letter.tex', 'paper_a2/main_zh.tex']

PLAN = [
    ('paper_a2/main.tex',
     'the public repository companion to this paper',
     'the repository companion to this paper (currently private; to be made public upon publication)'),
    ('paper_a2/cover_letter.tex',
     'are in the public repository',
     'are in the project repository (currently private; to be made public upon publication)'),
]

print('=== every occurrence of the offending phrase, with context ===')
contexts = {}
for rel in FILES:
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    with io.open(p, encoding='utf-8') as f:
        t = f.read()
    contexts[rel] = t
    found = [m.start() for m in re.finditer(r'public repository|公开仓库|公共仓库', t)]
    print('%-28s %d occurrence(s)' % (rel, len(found)))
    for i in found:
        snippet = re.sub(r'\s+', ' ', t[max(0, i - 150):i + 190])
        print('    ...' + snippet + '...')
print('')

failed = []
for rel, old, new in PLAN:
    t = contexts[rel]
    n = t.count(old)
    if n != 1:
        print('SKIP %s: expected 1 occurrence of %r, found %d' % (rel, old[:48], n))
        failed.append(rel)
        continue
    contexts[rel] = t.replace(old, new)
    print('OK   %s: replaced' % rel)

# the Chinese mirror, handled by phrase rather than by sentence
zh = contexts['paper_a2/main_zh.tex']
if '公开仓库' in zh:
    n = zh.count('公开仓库')
    zh = zh.replace('公开仓库', '项目仓库（当前为私有，发表后公开）')
    contexts['paper_a2/main_zh.tex'] = zh
    print('OK   paper_a2/main_zh.tex: %d occurrence(s) of 公开仓库 corrected' % n)
elif '公共仓库' in zh:
    n = zh.count('公共仓库')
    zh = zh.replace('公共仓库', '项目仓库（当前为私有，发表后公开）')
    contexts['paper_a2/main_zh.tex'] = zh
    print('OK   paper_a2/main_zh.tex: %d occurrence(s) of 公共仓库 corrected' % n)
else:
    print('NOTE paper_a2/main_zh.tex: no Chinese phrase for a public repository found')

if failed:
    print('')
    print('NOT WRITTEN because a target string did not match: %s' % ', '.join(failed))
    sys.exit(2)

for rel in FILES:
    with io.open(os.path.join(ROOT, rel.replace('/', os.sep)), 'w', encoding='utf-8', newline='\n') as f:
        f.write(contexts[rel])

print('')
print('=== verification after writing ===')
for rel in FILES:
    with io.open(os.path.join(ROOT, rel.replace('/', os.sep)), encoding='utf-8') as f:
        t = f.read()
    bad = 'public repository' in t or '公开仓库' in t or '公共仓库' in t
    print('%-28s still claims a public repository: %s' % (rel, bad))

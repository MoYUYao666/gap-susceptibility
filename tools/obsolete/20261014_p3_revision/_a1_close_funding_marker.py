# -*- coding: utf-8 -*-
"""Record the author's funding confirmation (2026-09-16) in the A1 masters.

The two `% AUTHOR: confirm ...` comments in each A1 master carry identical text, so
they cannot be told apart by string matching; each one is located by the section
heading that immediately follows it.  Only the Funding one is closed here -- the
generative-AI one stays open until the author confirms the tool names.
Also closes the Funding item in docs/A1_VENUE_DECISION.md."""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = '% AUTHOR: confirm'
NEW_FUNDING = ('% AUTHOR CONFIRMED 2026-09-16: the author has no funding sources. '
               'This statement is accurate as written.')
FUND_KEYS = ('Funding', '基金', '资助')

def lines(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read().split('\n')

def save(p, ls):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(ls))

changed = []

for rel in ('paper_a1/main.tex', 'paper_a1/main_zh.tex'):
    path = os.path.join(ROOT, rel)
    ls = lines(path)
    hits = []
    for i, line in enumerate(ls):
        if MARK not in line:
            continue
        nxt = ''
        for j in range(i + 1, min(i + 4, len(ls))):
            if ls[j].strip():
                nxt = ls[j]
                break
        if any(k in nxt for k in FUND_KEYS):
            hits.append((i, nxt.strip()[:60]))
    if len(hits) != 1:
        print('ABORT %s: expected exactly 1 funding marker, found %d %s' % (rel, len(hits), hits))
        sys.exit(1)
    idx, nxt = hits[0]
    ls[idx] = NEW_FUNDING
    save(path, ls)
    changed.append('  OK  %s line %d (was above: %s)' % (rel, idx + 1, nxt))

# close the funding item in the venue decision record
doc = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')
ls = lines(doc)
hit = [i for i, line in enumerate(ls) if line.startswith('1. **资助**')]
if len(hit) != 1:
    print('ABORT docs/A1_VENUE_DECISION.md: expected 1 funding item, found %d' % len(hit))
    sys.exit(1)
ls[hit[0]] = ('1. **资助（已确认）**：作者于 2026-09-16 确认**无任何基金、奖学金或项目资助**，'
              '故两篇稿件中的 "This research did not receive any specific grant from funding '
              'agencies in the public, commercial, or not-for-profit sectors." 与实际情况一致。'
              'A1 资助声明上方的确认标记已改为 `% AUTHOR CONFIRMED 2026-09-16`。')
save(doc, ls)
changed.append('  OK  docs/A1_VENUE_DECISION.md line %d (funding item closed)' % (hit[0] + 1))

print('applied %d change(s):' % len(changed))
for c in changed:
    print(c)

# report what is still open
print('')
for rel in ('paper_a1/main.tex', 'paper_a1/main_zh.tex'):
    ls = lines(os.path.join(ROOT, rel))
    open_marks = [i + 1 for i, l in enumerate(ls) if MARK in l]
    print('%s -- still-open AUTHOR markers at line(s): %s' % (rel, open_marks or 'none'))

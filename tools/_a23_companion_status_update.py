# -*- coding: utf-8 -*-
"""Trigger fired: A1 has been submitted (Neurocomputing, NEUCOM-D-26-20952, 2026-09-16).

docs/A1_VENUE_DECISION.md section 5 pre-wrote three A23 edits to apply once A1 was
actually submitted and before A23 is submitted.  Until now A23 said the companion's
revised version "is in preparation for resubmission elsewhere", which is no longer true.

The manuscript number is included so the companion is unambiguously identifiable -- the
editor of one Elsevier journal can look up a submission at another directly."""
import io
import os
import glob
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = 'NEUCOM-D-26-20952'

PLAN = [
    ('paper_a2/cover_letter.tex',
     '(decision received; a revised version is in preparation for resubmission elsewhere)',
     '(subsequently revised and submitted to \\emph{Neurocomputing}, manuscript %s)' % NUM,
     'cover letter: companion status updated'),
    ('paper_a2/main.tex',
     '(decision received); a revised version is in preparation for resubmission elsewhere.',
     'The revised manuscript has been submitted to Neurocomputing (manuscript %s).' % NUM,
     'main.tex wan2026a: companion status updated'),
    ('paper_a2/main_zh.tex',
     '（已收到决定）；修订版正在准备另投他刊.',
     '修订版已投 Neurocomputing（稿件编号 %s）。' % NUM,
     'main_zh.tex wan2026a: companion status updated'),
]

# first: is the stale wording present anywhere else in the A23 sources?
print('=== any other place in paper_a2 that still says "in preparation" ===')
for path in glob.glob(os.path.join(ROOT, 'paper_a2', '*.tex')):
    with io.open(path, encoding='utf-8') as f:
        t = f.read()
    for probe in ('in preparation for resubmission', '正在准备另投', 'resubmission elsewhere'):
        if probe in t:
            print('  %-28s contains %r' % (os.path.basename(path), probe))
print('')

for rel, old, new, label in PLAN:
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    with io.open(p, encoding='utf-8') as f:
        t = f.read()
    n = t.count(old)
    if n != 1:
        print('ABORT %s: expected 1 occurrence of the stale wording, found %d' % (rel, n))
        sys.exit(1)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t.replace(old, new))
    print('  OK  %s' % label)

# nothing stale may survive
leftover = []
for path in glob.glob(os.path.join(ROOT, 'paper_a2', '*.tex')):
    with io.open(path, encoding='utf-8') as f:
        t = f.read()
    if 'in preparation for resubmission' in t or '正在准备另投' in t:
        leftover.append(os.path.basename(path))
if leftover:
    print('ABORT: stale wording survives in %s' % ', '.join(leftover))
    sys.exit(1)
print('  OK  no stale companion-status wording remains in paper_a2/*.tex')

# record the trigger as discharged
doc = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')
with io.open(doc, encoding='utf-8') as f:
    d = f.read()
old = '**状态：措辞已拟好，尚未写入**'
if old not in d:
    print('ABORT: could not find the status line in the venue record')
    sys.exit(1)
d = d.replace(old, '**状态：已于 2026-09-16 应用**（A1 提交号为 %s），原状态为' % NUM, 1)
d += """
## 十一、A1 已提交（2026-09-16）与 A23 的连带更新（已执行）

**A1 提交号：`%s`**（Neurocomputing，提交时间 2026-09-16 04:58，状态 Submitted to Journal）。

第五节预设的触发条件已满足，三处 A23 文字已按预写措辞更新，并**加入该提交号**以便同一出版社的
编辑可直接检索该同伴稿：

- `paper_a2/cover_letter.tex:32` → "(subsequently revised and submitted to \\emph{Neurocomputing}, manuscript %s)"
- `paper_a2/main.tex:880`（`wan2026a`） → "The revised manuscript has been submitted to Neurocomputing (manuscript %s)."
- `paper_a2/main_zh.tex:748`（`wan2026a`） → 「修订版已投 Neurocomputing（稿件编号 %s）。」

已核验 `paper_a2/*.tex` 中**不再有**"in preparation for resubmission"/「正在准备另投」这类过期表述。

**由此 A23 可以提交**：其投稿包中的主稿、封面信与参考文献现在对同伴稿的陈述与事实一致。
""" % (NUM, NUM, NUM, NUM)

with io.open(doc, 'w', encoding='utf-8', newline='\n') as f:
    f.write(d)
print('  OK  docs/A1_VENUE_DECISION.md: trigger recorded as discharged (section 11)')

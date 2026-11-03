# -*- coding: utf-8 -*-
"""A1 -> Neurocomputing: restore the task-sensitivity sentence in the abstract,
switch the four figures to vector PDF, and correct the data-availability wording
now that the repository is public.

Every replacement asserts an exact expected hit count; anything unexpected aborts
before any write, so a partial edit is impossible."""
import io, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(ROOT, 'paper_a1', 'main.tex')
ZH   = os.path.join(ROOT, 'paper_a1', 'main_zh.tex')

def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()

def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

def rep(text, old, new, expect, label, log):
    n = text.count(old)
    if n != expect:
        print('ABORT: %s -- expected %d occurrence(s), found %d' % (label, expect, n))
        sys.exit(1)
    log.append('  OK  %-46s x%d' % (label, n))
    return text.replace(old, new)

edits = []
en = read(MAIN)
zh = read(ZH)

# --- 1. abstract: restore the task-sensitivity ordering, pay for it with prose trims
en = rep(en,
    'in alignment methods and gap-based quantities predict retrieval degradation',
    'and gap-based quantities predict retrieval degradation',
    1, 'abstract: drop "in alignment methods" (-3 w)', edits)
en = rep(en,
    'by the legacy training-time logger on its hold-out; we quote the range and name the protocol rather than the larger value',
    'by the legacy logger on its hold-out; we quote the range and the protocol, not the larger value',
    1, 'abstract: legacy logger + quote-the-range (-4 w)', edits)
en = rep(en,
    'and predicts, as we confirm, markedly less destruction from text-side than image-side translation.',
    'and predicts, as we confirm, less destruction from text-side than image-side translation.',
    1, 'abstract: shorten theory prediction (-1 w)', edits)
en = rep(en,
    'the gap for retrieval; we claim this for no other families, benchmarks or adaptation mechanisms.',
    ('the gap for retrieval, giving a task-sensitivity ordering '
     '(centroid classification $<$ zero-shot classification $<$ retrieval); '
     'we claim this for no other families, benchmarks or mechanisms.'),
    1, 'abstract: RESTORE task-sensitivity ordering (+12 w)', edits)

# --- 2. figures -> vector PDF
for fig in ('fig1_lambda', 'fig2_tau_top1', 'fig3_trajectory', 'fig4_spectrum'):
    en = rep(en, 'figures/%s.png' % fig, 'figures/%s.pdf' % fig, 1, 'en includegraphics %s -> .pdf' % fig, edits)
    zh = rep(zh, 'figures/%s.png' % fig, 'figures/%s.pdf' % fig, 1, 'zh includegraphics %s -> .pdf' % fig, edits)

# --- 3. data availability: the repository is public
en = rep(en,
    '(reproducibility archive upon publication)',
    '(public repository)',
    1, 'en data availability -> public repository', edits)
zh = rep(zh,
    '（论文发表后公开可复现档案）',
    '（公开仓库）',
    1, 'zh data availability -> public repository', edits)

write(MAIN, en)
write(ZH, zh)

print('applied %d replacements:' % len(edits))
for e in edits:
    print(e)

# --- report on the ZH abstract so a mirror can be decided
zabs = zh.split('\\begin{abstract}', 1)[-1].split('\\end{abstract}', 1)[0]
print('')
print('ZH abstract present: %s' % ('yes' if zabs.strip() else 'no'))
print('ZH abstract contains the ordering already: %s'
      % ('yes' if ('<' in zabs and ('质心' in zabs or 'centroid' in zabs)) else 'NO -- needs mirroring'))

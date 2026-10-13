# -*- coding: utf-8 -*-
"""The repository is private, not public.

The operator confirmed "public" earlier, so the manuscript and the cover letter were both
changed to describe a public repository.  That is now known to be wrong and would have been
an untrue statement in a submitted manuscript, so both are restored to wording that is
accurate for a private repository whose archive is released at publication
(Elsevier's research-data policy expressly allows a stated reason when data cannot be
accessed at submission).

Also corrects the two places in docs/A1_VENUE_DECISION.md that recorded the repository as
public, and records the operator's correction so a later session does not re-apply it."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAIN = os.path.join(ROOT, 'paper_a1', 'main.tex')
ZH = os.path.join(ROOT, 'paper_a1', 'main_zh.tex')
CL = os.path.join(ROOT, 'paper_a1', 'cover_letter.tex')
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

REPLACEMENTS = [
    (MAIN, '(public repository)',
     '(reproducibility archive upon publication)',
     'main.tex: data availability restored to the private-repository wording'),
    (ZH, '（公开仓库）',
     '（论文发表后公开可复现档案）',
     'main_zh.tex: 同步恢复'),
    (CL, 'The code, the archived result files and the figure-generation scripts for this study '
         'are available in a public repository at \\texttt{github.com/MoYUYao666/gap-susceptibility}.',
     'All data, code, and checkpoints used in this study are archived and will be released upon publication.',
     'cover_letter.tex: restored, with "publication" rather than "acceptance" so it matches the manuscript'),
]

log = []
for path, old, new, label in REPLACEMENTS:
    with io.open(path, encoding='utf-8') as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        print('ABORT: %s -- expected 1 occurrence, found %d' % (label, n))
        sys.exit(1)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text.replace(old, new))
    log.append('  OK  ' + label)

# no claim of a public repository may survive in the submitted files
for path in (MAIN, ZH, CL):
    with io.open(path, encoding='utf-8') as f:
        t = f.read()
    for bad in ('public repository', 'public repo', '公开仓库', 'publicly available'):
        if bad in t:
            print('ABORT: %s still contains %r' % (os.path.basename(path), bad))
            sys.exit(1)
log.append('  OK  verified: no "public repository" claim left in main.tex / main_zh.tex / cover_letter.tex')

# correct the decision record
with io.open(DOC, encoding='utf-8') as f:
    lines = f.read().split('\n')

fixed = 0
for i, line in enumerate(lines):
    if line.startswith('3. **仓库公开状态'):
        lines[i] = ('3. **仓库公开状态（已更正）**：作者 2026-09-16 更正为 **仓库目前仍是 private**。'
                    '因此正文与 cover letter 中"public repository / 公开仓库"的表述**已全部撤回**，'
                    '恢复为 "reproducibility archive upon publication"（`paper_a1/main.tex:578`、'
                    '`main_zh.tex:581`）与 "will be released upon publication"（`cover_letter.tex`）。'
                    'Elsevier 的数据政策允许在投稿时说明数据暂不可访问的原因，故此表述合规。'
                    '**若将来把仓库转为 public，才可改回直接可访问的说法。**')
        fixed += 1
    elif line.startswith('**同时修正的不一致**'):
        lines[i] = ('**同时修正的不一致**：cover letter 结尾原写 "All data, code, and checkpoints ... will be '
                    'released upon acceptance"，与正文的 "public repository" 说法矛盾。曾一度改为陈述公开仓库；'
                    '**在作者更正仓库仍为 private 后，该改动已撤回**，现为 "will be released upon publication"，'
                    '与正文一致。注意：`.pt` 检查点并不在仓库中，此句是对**将来发布**的承诺而非现状陈述。')
        fixed += 1

if fixed != 2:
    print('ABORT: expected to correct 2 lines in the decision record, corrected %d' % fixed)
    sys.exit(1)
with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
log.append('  OK  docs/A1_VENUE_DECISION.md: repository status corrected in 2 places')

print('applied:')
for line in log:
    print(line)

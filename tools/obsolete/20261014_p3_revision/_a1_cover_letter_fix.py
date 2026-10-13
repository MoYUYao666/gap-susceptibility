# -*- coding: utf-8 -*-
"""Two corrections to the A1 cover letter, plus a record of the operator's instruction.

1. Remove every mention of `paper_ap3`.  Per docs/PA_P3_MERGE_PLAN.md:3 it is not an
   independent companion manuscript: it is the merge of Paper A (itself P1+P2) with P3,
   and A1/A2 are explicitly excluded from that merge.  The trigger (a rejection of P1) has
   not fired, so it is a pending draft, not a companion study -- describing it as one was
   simply wrong.
2. The closing paragraph still promised that data and code "will be released upon
   acceptance", which now contradicts the manuscript, where the archive is described as a
   public repository.  State what is actually true, and do not claim the checkpoints are
   public: the repository carries code, archived result files and figure scripts, while the
   .pt checkpoints are not tracked there."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = os.path.join(ROOT, 'paper_a1', 'cover_letter.tex')
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

with io.open(CL, encoding='utf-8') as f:
    text = f.read()

PAIRS = [
    (' A second companion manuscript by the same author, ``Gradient Structure Laws as '
     'Predictors of PEFT Design: Alignment Dynamics and Cross-Architecture Rank '
     'Allocation\'\', is in preparation and has not yet been submitted to any journal. '
     'The present manuscript shares a motivating observation with the first of these but '
     'is a distinct contribution:',
     ' The present manuscript shares a motivating observation with it but is a distinct '
     'contribution:', 1, 'remove the paper_ap3 sentence'),
    ('All data, code, and checkpoints used in this study are archived and will be released '
     'upon acceptance.',
     'The code, the archived result files and the figure-generation scripts for this study '
     'are available in a public repository at \\texttt{github.com/MoYUYao666/gap-susceptibility}.',
     1, 'state the public repository instead of a promise on acceptance'),
]

log = []
for old, new, expect, label in PAIRS:
    n = text.count(old)
    if n != expect:
        print('ABORT: %s -- expected %d occurrence(s), found %d' % (label, expect, n))
        sys.exit(1)
    text = text.replace(old, new)
    log.append('  OK  %s' % label)

if 'Gradient Structure' in text or 'paper_ap3' in text or 'ap3' in text:
    print('ABORT: a mention of the merged manuscript survives in the cover letter')
    sys.exit(1)
log.append('  OK  verified: no mention of the merged manuscript remains')

with io.open(CL, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

with io.open(DOC, encoding='utf-8') as f:
    doc = f.read()

doc += """
## 九、不要在任何投稿件中提及 `paper_ap3`（2026-09-16，操作者指示）

**指示**：投稿件中不得提及 `paper_ap3`。

**事实核对**（`docs/PA_P3_MERGE_PLAN.md:3`，操作者 2026-09-04 决策）：`paper_ap3` 不是一篇独立的
"companion" 稿件，而是 **Paper A（其本身为 P1+P2 合并稿）与 P3 的合并稿**；该行同时明确
"**A1（PRL）与 A2（OE）保持独立不并入**"。触发条件是 **P1 被 PR 拒稿**；操作者 2026-09-16 确认
P1 仍在审 → **合并尚未启动**，`paper_ap3` 是一份待定草稿。

**据此执行的修改**：`paper_a1/cover_letter.tex` 原先用一整段把它描述为"另一位 companion 稿、
尚未投任何刊"——这既是指示禁止的提及，也是**事实描述错误**（它并非独立稿件）。已删除该句，并把
原句中的"the first of these"改为"it"，使段落仅保留对 **P1** 的披露（P1 在 PR 审稿中，且是本文引用
的先前工作，此项披露必须保留）。

**同时修正的不一致**：cover letter 结尾原写 "All data, code, and checkpoints ... will be released
upon acceptance"，与正文已改为 "public repository" 的说法矛盾。已改为陈述公开仓库（代码、归档结果
文件与绘图脚本），**并刻意不提 checkpoints 公开**——`.pt` 检查点并未纳入该仓库。

**给后续会话的约束**：A1/A23 的 cover letter、正文与参考文献中均不得出现 `paper_ap3` 的名称或标题。
`docs/` 内的审计记录可以继续引用它（那是内部记录，不随投稿提交）。
"""

with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(doc)

print('cover letter changes:')
for line in log:
    print(line)
print('')
print('docs/A1_VENUE_DECISION.md section 9 appended (%d chars)' % len(doc))

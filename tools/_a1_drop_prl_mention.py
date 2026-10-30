# -*- coding: utf-8 -*-
"""Operator decisions, 2026-09-16:
  * no preprint exists (asked and answered: "没有");
  * the prior Pattern Recognition Letters submission is NOT to be mentioned in A1's
    cover letter ("去掉") -- the guide requires only that the work is unpublished and
    not under consideration elsewhere, and both remain true without it;
  * the "decision received" signal is also dropped from A23's disclosure of the
    companion manuscript.

This removes the sentence, verifies that no mention of the manuscript number survives
anywhere in the A1 submission set, and updates the prepared A23 wording accordingly."""
import io
import os
import glob
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = os.path.join(ROOT, 'paper_a1', 'cover_letter.tex')
DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')

log = []

# --- 1. remove the sentence from the cover letter
with io.open(CL, encoding='utf-8') as f:
    cl = f.read()
OLD = (' This manuscript was previously submitted to \\textit{Pattern Recognition Letters} '
       '(manuscript PRLETTERS-D-26-01941); the decision declining it was received on '
       '14 September 2026.')
n = cl.count(OLD)
if n != 1:
    print('ABORT: expected 1 prior-submission sentence, found %d' % n)
    sys.exit(1)
cl = cl.replace(OLD, '')
if 'PRLETTERS' in cl or 'previously submitted' in cl:
    print('ABORT: a prior-submission mention survives in the cover letter')
    sys.exit(1)
with io.open(CL, 'w', encoding='utf-8', newline='\n') as f:
    f.write(cl)
log.append('  OK  cover_letter.tex: prior-submission sentence removed')

# --- 2. no manuscript number anywhere else in the submitted A1 sources
ALLOWED = ('related_work_bibitems.tex',)  # hu2025inferencecal is published in PRL; a citation, not a disclosure
bad = []
for path in glob.glob(os.path.join(ROOT, 'paper_a1', '*.tex')):
    with io.open(path, encoding='utf-8') as f:
        t = f.read()
    if 'PRLETTERS' in t:
        bad.append(os.path.basename(path))
if bad:
    print('ABORT: the manuscript number still appears in: %s' % ', '.join(bad))
    sys.exit(1)
log.append('  OK  no PRLETTERS number anywhere in paper_a1/*.tex')
with io.open(os.path.join(ROOT, 'paper_a1', 'related_work_bibitems.tex'), encoding='utf-8') as f:
    if 'Pattern Recognition Letters' in f.read():
        log.append('  NOTE related_work_bibitems.tex still names PRL as the venue of a cited '
                   'paper (hu2025inferencecal) -- that is citation data, kept deliberately')

# --- 3. drop "decision received" from the prepared A23 wording
with io.open(DOC, encoding='utf-8') as f:
    doc = f.read()
PAIRS = [
    ('(decision received; the revised manuscript has been submitted to \\emph{Neurocomputing})',
     '(subsequently revised and submitted to \\emph{Neurocomputing})',
     'cover_letter.tex:32 replacement'),
    ('(decision received); the revised manuscript has been submitted to Neurocomputing.',
     'The revised manuscript has been submitted to Neurocomputing.',
     'main.tex wan2026a replacement'),
    ('（已收到决定）；修订版已投 Neurocomputing.',
     '修订版已投 Neurocomputing.',
     'main_zh.tex wan2026a replacement'),
]
for old, new, label in PAIRS:
    if doc.count(old) != 1:
        print('ABORT: %s -- expected 1 occurrence, found %d' % (label, doc.count(old)))
        sys.exit(1)
    doc = doc.replace(old, new)
    log.append('  OK  prepared wording updated: ' + label)

doc += """
## 十、A1 不再提及 PRL 前次投稿（2026-09-16，操作者决定）

**决定**：A1 的 cover letter **不提及**曾被 Pattern Recognition Letters 拒稿一事。已删除原句
"This manuscript was previously submitted to *Pattern Recognition Letters* (manuscript
PRLETTERS-D-26-01941); the decision declining it was received on 14 September 2026."，并核验
`paper_a1/*.tex` 中**不再出现该稿号**。

**依据**：Neurocomputing 的 Guide 只要求两条声明——`:252`（未发表过，预印本等形式除外）与 `:256`
（未在他刊审理中）。**Guide 无"披露前次投稿或被拒"的条款**；唯一涉及稿件流转的是 Elsevier 的
Article Transfer Service（`:1273-1275`），操作者选择不走 ATS。删除后两条强制声明仍然为真，故
不构成不实陈述。留着只会在编辑读稿前立起"上一家拒了"的锚点，而回应 PRL 审稿人的整改工作在本稿中
不可见（`revision_additions.tex` 未被 `\\input`），读者看不到"已大幅改进"。

**硬底线**：若投稿系统或编辑**直接询问**是否曾投他刊/是否曾被拒，必须如实回答，不得在直接提问下
作虚假陈述；届时应一并给出整改与新增实验的说明（材料见 `A1_REVIEWER_RESPONSE_PLAN.md`
与 `A1_RESUBMISSION_MASTER_PLAN.md`）。

**预印本**：操作者 2026-09-16 确认**不存在任何预印本**（arXiv 或其他平台）。若将来挂出预印本，
Guide `:252` 明确允许，但应在 cover letter 中如实说明（同时也是对相似度检测命中的预防）。

**连带修改**：A23 中对同伴稿（A1）的披露，原含 "decision received"（读者会推断被拒），已在预写
措辞中一并去掉，改为 "subsequently revised and submitted to Neurocomputing" / "The revised
manuscript has been submitted to Neurocomputing." / 「修订版已投 Neurocomputing.」。注意 A23 保留
"previously submitted to Pattern Recognition Letters" 作为该同伴稿的**识别信息**，这一点仍是事实陈述。
"""

with io.open(DOC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(doc)
log.append('  OK  docs/A1_VENUE_DECISION.md: section 10 appended')

print('applied:')
for line in log:
    print(line)

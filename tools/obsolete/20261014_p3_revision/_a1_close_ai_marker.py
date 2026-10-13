# -*- coding: utf-8 -*-
"""Close the last four `% AUTHOR: confirm` markers (generative-AI declaration) after
the author confirmed the tool names and scope on 2026-09-16, and close the two
remaining open items in docs/A1_VENUE_DECISION.md.

After the funding marker was closed earlier, each of the four manuscripts carries
exactly one `AUTHOR: confirm` marker, so a line-level replacement is unambiguous --
the count is asserted per file."""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = 'AUTHOR: confirm'
NEW = ('% AUTHOR CONFIRMED 2026-09-16: the author confirms that the tool names and the '
       'scope of this declaration are accurate as written.')

FILES = ('paper_a1/main.tex', 'paper_a1/main_zh.tex', 'paper_a2/main.tex', 'paper_a2/main_zh.tex')

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read().split('\n')

def save(p, ls):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(ls))

changed = []
for rel in FILES:
    path = os.path.join(ROOT, rel)
    ls = load(path)
    hits = [i for i, line in enumerate(ls) if MARK in line]
    if len(hits) != 1:
        print('ABORT %s: expected exactly 1 open marker, found %d at %s' % (rel, len(hits), [h + 1 for h in hits]))
        sys.exit(1)
    old = ls[hits[0]].strip()
    ls[hits[0]] = NEW
    save(path, ls)
    changed.append('  OK  %s line %d closed' % (rel, hits[0] + 1))
    changed.append('        was: %s' % old)

DOC = os.path.join(ROOT, 'docs', 'A1_VENUE_DECISION.md')
ls = load(DOC)
for prefix, new_text in (
    ('2. **AI 声明口径**',
     '2. **AI 声明口径（已确认）**：作者于 2026-09-16 确认生成式 AI 声明的**工具名与范围**表述准确。'
     '四份主文件（`paper_a1/main.tex:587`、`main_zh.tex:590`、`paper_a2/main.tex:832`、`main_zh.tex:721`）'
     '的 `% AUTHOR: confirm` 标记已改为 `% AUTHOR CONFIRMED 2026-09-16`。'
     '依据为项目自身记录：`SUBMISSION_CHECKLIST.md:27`（"Claude + DeepSeek"）与旧 `declaration.pdf` 原文。'),
    ('3. **仓库公开状态**',
     '3. **仓库公开状态（已确认）**：作者确认 `github.com/OWNER/gap-susceptibility` 为 **public**，'
     '故正文的代码与数据表述已由 "reproducibility archive upon publication" 改为 "public repository"'
     '（`paper_a1/main.tex:578`、`main_zh.tex:581`）。'),
):
    hit = [i for i, line in enumerate(ls) if line.startswith(prefix)]
    if len(hit) != 1:
        print('ABORT %s: expected 1 item starting with %r, found %d' % (os.path.basename(DOC), prefix, len(hit)))
        sys.exit(1)
    ls[hit[0]] = new_text
    changed.append('  OK  docs/A1_VENUE_DECISION.md line %d closed (%s)' % (hit[0] + 1, prefix[:12]))
save(DOC, ls)

print('applied:')
for c in changed:
    print(c)

print('')
left = 0
for rel in FILES:
    ls = load(os.path.join(ROOT, rel))
    left += sum(1 for l in ls if MARK in l)
print('remaining open AUTHOR: confirm markers across all four masters: %d' % left)

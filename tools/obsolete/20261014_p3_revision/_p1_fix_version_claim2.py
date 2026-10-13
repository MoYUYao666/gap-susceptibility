# -*- coding: utf-8 -*-
'''
Stop asserting that the 14 August corrections failed to take effect.

The operator states a round of corrections was submitted on 14 August. The Desktop copy is
the ORIGINAL submission snapshot (built 24 July), which is what EM keeps for the submission
item regardless of later replacements; its contents tell us what the first submission said,
not whether the replacements were processed.

Note to self: the previous attempt died at parse time because the Chinese text contained
ASCII double quotes inside a double-quoted Python string, and the shell chain then committed
anyway. This version uses single-quoted strings and full-width quotes inside the text, and it
verifies each replacement before writing.
'''
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"

LOG_OLD = '**结论：8-14 的两次更正显然没有替换掉 EM 里的稿件**（快照仍是 7-24 版，既不含 59.37/58.76 也不含 59.28/58.66）。→'
LOG_NEW = ('**关于版本状态的记录（按操作者说明，2026-09-20）**：8-14 已提交过一轮更正。桌面这份是**首次提交**的'
           '合并产物——EM 对提交件保留的通常就是首次生成的那份，是否被后续替换件覆盖，从这份 PDF 看不出来，'
           '**不据此推断**。因此下表列的是“**首次提交 → 现稿**”的差异，供返修时逐条对照。→')

H_OLD = '**8-14 两次更正显然未替换成功**。返修封面信已按该版本'
H_NEW = ('8-14 已按操作者说明提交过一轮更正；桌面这份是**首次提交**的合并产物，不据此推断替换是否生效。'
         '返修封面信已按该版本')

SPEC_OLD = ("'Version on file: the manuscript in Editorial Manager is still the 24 July 2026 "
            "snapshot, which reports 24%%, 53.3%%/1.7%%/+0.079, CIFAR-100, 116 experiments and "
            "r=-0.827/-0.807. The revision cover letter reconciles that version against this "
            "one row by row.',")
SPEC_NEW = ("'Version history: the original submission is dated 24 July 2026 and reported 24%%, "
            "53.3%%/1.7%%/+0.079, CIFAR-100, 116 experiments and r=-0.827/-0.807; a round of "
            "corrections followed on 14 August. The revision cover letter reconciles the "
            "original submission against this revision row by row.',")

EDITS = [
    ('paper/cover_letter_revision.tex',
     '\\textbf{Which version this letter concerns.} The manuscript currently in Editorial Manager is the 24 July 2026 submission snapshot. Two correction letters dated 14 August followed;',
     '\\textbf{Which version this letter concerns.} The original submission is dated 24 July 2026 and was followed by a round of corrections on 14 August;'),
    ('docs/P1_REMEDIATION_LOG.md', LOG_OLD, LOG_NEW),
    ('HANDOFF.md', H_OLD, H_NEW),
    ('tools/build_submission_packages.py', SPEC_OLD, SPEC_NEW),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    s = io.open(p, encoding='utf-8').read()
    n = s.count(old)
    if n != 1:
        fails.append('%s: found %d' % (rel, n))
        print('FAIL %s (%d)' % (rel, n))
        continue
    io.open(p, 'w', encoding='utf-8', newline='').write(s.replace(old, new, 1))
    print('ok   %s' % rel)
if fails:
    print(fails)
    sys.exit(1)
print('WORDING CORRECTED')

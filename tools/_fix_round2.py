# -*- coding: utf-8 -*-
"""Round 2 of the audit fixes.

1. paper_a2/main.tex had TWO claims that the project repository is public; the first pass
   replaced only one, and its own verification printed "still claims: True" without acting
   on it.  Close the second occurrence (and make the check fatal this time).
2. tools/audit_submission_pdfs.py itself was stale: it looked for cover_letter.pdf while
   the generator now emits "Cover letter.pdf" to match the submission slot, and it treated
   the A23 companion-manuscript number as forbidden when that number is a required part of
   the A23 disclosure.  Also: a manuscript need not print the journal name, so that check
   belongs on the cover letter only."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(rel):
    with io.open(os.path.join(ROOT, rel.replace('/', os.sep)), encoding='utf-8') as f:
        return f.read()

def save(rel, t):
    with io.open(os.path.join(ROOT, rel.replace('/', os.sep)), 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)

def rep(t, old, new, expect, label):
    n = t.count(old)
    if n != expect:
        print('ABORT: %s -- expected %d occurrence(s), found %d' % (label, expect, n))
        sys.exit(1)
    print('  OK  %s' % label)
    return t.replace(old, new)

# ---- 1. the second false claim in the A23 manuscript
p = 'paper_a2/main.tex'
t = load(p)
t = rep(t, 'are available in the public repository',
        'are archived in the project repository (currently private; to be made public upon publication)',
        1, 'A23 main.tex: second public-repository claim corrected')
if 'public repository' in t or 'publicly available' in t:
    print('ABORT: a public-availability claim survives in %s' % p)
    sys.exit(1)
print('  OK  %s: no public-availability claim left' % p)
save(p, t)

# ---- 2. the audit script (filename, allowance, journal check)
a = 'tools/audit_submission_pdfs.py'
t = load(a)
t = rep(t, "'cover_letter.pdf'", "'Cover letter.pdf'", 2, 'audit: expects the upload-slot filename')
t = rep(t,
        "FORBIDDEN = ['paper_ap3', 'Gradient Structure', 'PRLETTERS', 'public repository', '公开仓库',\n"
        "             'TODO', 'FIXME', 'XXX', 'PLACEHOLDER', 'lorem ipsum']",
        "FORBIDDEN = ['paper_ap3', 'Gradient Structure', 'PRLETTERS', 'public repository', '公开仓库',\n"
        "             'TODO', 'FIXME', 'XXX', 'PLACEHOLDER', 'lorem ipsum']\n"
        "\n"
        "# A23 legitimately names the companion manuscript number PRLETTERS-D-26-01941 in its\n"
        "# disclosure of that companion; it is the A1 submission that must never mention it.\n"
        "ALLOWED_PER_SET = {'A23 -> Ocean Engineering': ['PRLETTERS']}",
        1, 'audit: allowance table added')
t = rep(t, '        hits = [bad for bad in FORBIDDEN if bad in flat]',
        '        hits = [bad for bad in FORBIDDEN if bad in flat\n'
        "                and bad not in ALLOWED_PER_SET.get(label, [])]",
        1, 'audit: allowance applied')
t = rep(t, "        if name in ('main.pdf', 'Cover letter.pdf') and not jrn:",
        "        if name == 'Cover letter.pdf' and not jrn:",
        1, 'audit: journal name required on the cover letter only')
save(a, t)
print('  OK  audit script updated')
print('')
print('round 2 applied')

# -*- coding: utf-8 -*-
"""Patch tools/audit_submission_pdfs.py only (the previous attempt aborted on a miscount:
'cover_letter.pdf' occurs three times, not two, so nothing was written).

Three corrections:
  * the generator now emits "Cover letter.pdf" to match the submission slot;
  * A23 legitimately names the companion manuscript number, so PRLETTERS is allowed there
    and forbidden only in A1;
  * a manuscript need not print the journal name, so that requirement belongs to the cover
    letter alone."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = 'tools/audit_submission_pdfs.py'
p = os.path.join(ROOT, REL.replace('/', os.sep))

with io.open(p, encoding='utf-8') as f:
    t = f.read()

def rep(old, new, expect, label):
    global t
    n = t.count(old)
    if n != expect:
        print('ABORT: %s -- expected %d, found %d' % (label, expect, n))
        sys.exit(1)
    t = t.replace(old, new)
    print('  OK  %s' % label)

rep("'cover_letter.pdf'", "'Cover letter.pdf'", 3, 'filename matches the upload slot (3 sites)')

rep("FORBIDDEN = ['paper_ap3', 'Gradient Structure', 'PRLETTERS', 'public repository', '公开仓库',\n"
    "             'TODO', 'FIXME', 'XXX', 'PLACEHOLDER', 'lorem ipsum']",
    "FORBIDDEN = ['paper_ap3', 'Gradient Structure', 'PRLETTERS', 'public repository', '公开仓库',\n"
    "             'TODO', 'FIXME', 'XXX', 'PLACEHOLDER', 'lorem ipsum']\n"
    "\n"
    "# A23 must name the companion manuscript number PRLETTERS-D-26-01941 when it discloses\n"
    "# that companion; the A1 submission is the one that must never mention it.\n"
    "ALLOWED_PER_SET = {'A23 -> Ocean Engineering': ['PRLETTERS']}",
    1, 'allowance table added')

rep('        hits = [bad for bad in FORBIDDEN if bad in flat]',
    '        hits = [bad for bad in FORBIDDEN if bad in flat\n'
    "                and bad not in ALLOWED_PER_SET.get(label, [])]",
    1, 'allowance applied to the scan')

rep("        if name in ('main.pdf', 'Cover letter.pdf') and not jrn:",
    "        if name == 'Cover letter.pdf' and not jrn:",
    1, 'journal name required on the cover letter only')

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(t)

print('')
print('=== resulting checks, for the record ===')
for i, line in enumerate(t.split('\n'), 1):
    if 'Cover letter.pdf' in line or 'ALLOWED_PER_SET' in line:
        print('  %4d: %s' % (i, line.rstrip()))

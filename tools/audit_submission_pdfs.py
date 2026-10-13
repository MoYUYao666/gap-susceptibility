# -*- coding: utf-8 -*-
"""Final pre-submission audit of every PDF in the three submission folders.

Checks things that only show up in a built PDF rather than in the .tex sources: stray
placeholders, undefined cross-references rendered as ??/[?], any mention of material that
must not appear, the author block, the journal name, page counts, and -- importantly --
whether the figures actually got embedded (A1's are now vector PDFs, so its main file
should carry no raster image at all, while A23's and P1's figure PNGs should all be present).

2026-09-20: the P1 package was previously not audited at all, and the author/email/raster
checks were hard-coded to the file name 'main.pdf', which P1's manuscript (main_nn.pdf) does
not use.  The manuscript and cover letter are now identified per set, and P1 is included
(measured 25 raster images and 43 pages in main_nn.pdf)."""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = r'D:\texlive\2025\bin\windows'
PDFINFO = os.path.join(BIN, 'pdfinfo.exe')
PDFTOTEXT = os.path.join(BIN, 'pdftotext.exe')
PDFIMAGES = os.path.join(BIN, 'pdfimages.exe')

# (label, folder, journal, files, minimum embedded raster images; files[0] is the manuscript)
SETS = [
    ('A1 -> Neurocomputing', 'SUBMISSION/A1_Neurocomputing', 'Neurocomputing',
     ['main.pdf', 'Cover letter.pdf', 'highlights.pdf', 'declaration.pdf', 'abstract.pdf'], 0),
    ('A23 -> Ocean Engineering', 'SUBMISSION/A23_OceanEngineering', 'Ocean Engineering',
     ['main.pdf', 'Cover letter.pdf', 'highlights.pdf', 'abstract.pdf'], 7),
    ('P1 -> Pattern Recognition', 'SUBMISSION/P1_PatternRecognition', 'Pattern Recognition',
     ['main_nn.pdf', 'cover_letter_revision.pdf', 'highlights.pdf', 'declaration.pdf'], 20),
]

FORBIDDEN = ['paper_ap3', 'Gradient Structure', 'PRLETTERS', 'public repository', '公开仓库',
             'TODO', 'FIXME', 'XXX', 'PLACEHOLDER', 'lorem ipsum']

# A23 must name the companion manuscript number PRLETTERS-D-26-01941 when it discloses
# that companion; the A1 submission is the one that must never mention it.
ALLOWED_PER_SET = {'A23 -> Ocean Engineering': ['PRLETTERS']}


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.stdout.decode('utf-8', 'replace')


def pages(pdf):
    m = re.search(r'Pages:\s+(\d+)', run([PDFINFO, pdf]))
    return m.group(1) if m else '?'


def text(pdf):
    tmp = os.path.join(ROOT, '_audit_tmp.txt')
    run([PDFTOTEXT, '-layout', pdf, tmp])
    if os.path.isfile(tmp):
        with io.open(tmp, encoding='utf-8', errors='replace') as f:
            t = f.read()
        os.remove(tmp)
        return t
    return ''


def raster_count(pdf):
    out = run([PDFIMAGES, '-list', pdf])
    return len([l for l in out.split('\n') if re.match(r'^\s*\d+\s+\d+', l)])


problems = []
print('=' * 96)
for label, folder, journal, files, expect_raster in SETS:
    main_name = files[0]
    cover_name = next((f for f in files if 'over letter' in f or f.startswith('cover_letter')), None)
    print('%s   (%s)' % (label, folder))
    print('-' * 96)
    for name in files:
        p = os.path.join(ROOT, folder.replace('/', os.sep), name)
        if not os.path.isfile(p):
            print('  %-20s  MISSING' % name)
            problems.append('%s/%s missing' % (folder, name))
            continue
        t = text(p)
        flat = re.sub(r'\s+', ' ', t)
        hits = [bad for bad in FORBIDDEN if bad in flat
                and bad not in ALLOWED_PER_SET.get(label, [])]
        undefined = flat.count('??') + flat.count('[?]')
        who = all(s in flat for s in ('Hongrui Wan', 'Southampton'))
        mail = 'contact@example.com' in flat
        jrn = journal in flat
        ras = raster_count(p)
        size = os.path.getsize(p)
        flags = []
        if hits:
            flags.append('FORBIDDEN:' + ','.join(hits))
            problems.append('%s/%s contains %s' % (folder, name, hits))
        if undefined:
            flags.append('UNDEFINED-x%d' % undefined)
            problems.append('%s/%s has %d undefined marker(s)' % (folder, name, undefined))
        if name == main_name and not who:
            flags.append('AUTHOR-BLOCK?')
            problems.append('%s/%s: author/affiliation text not found' % (folder, name))
        if name == main_name and not mail:
            flags.append('EMAIL?')
        if name == cover_name and not jrn:
            flags.append('JOURNAL-NAME?')
            problems.append('%s/%s does not name %s' % (folder, name, journal))
        if name == main_name:
            if expect_raster == 0 and ras != 0:
                flags.append('RASTER-FIGURES-x%d (expected 0: vector)' % ras)
                problems.append('%s/%s carries %d raster image(s)' % (folder, name, ras))
            if expect_raster and ras < expect_raster:
                flags.append('FIGURES-x%d (expected >=%d)' % (ras, expect_raster))
                problems.append('%s/%s embeds %d raster image(s), expected >=%d'
                                % (folder, name, ras, expect_raster))
        print('  %-20s %2s pp  %8.1f kB  raster=%-3d author=%-5s email=%-5s journal=%-5s  %s'
              % (name, pages(p), size / 1e3, ras, who, mail, jrn,
                 ('OK' if not flags else ' | '.join(flags))))
    print('')

print('=' * 96)
print('PROBLEMS: %d' % len(problems))
for p in problems:
    print('  - ' + p)
if not problems:
    print('  none')

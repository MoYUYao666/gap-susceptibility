# -*- coding: utf-8 -*-
"""paper合 overlap fix, part 1: replace the reprinted per-run catalogue with a section-level summary.

Why: paper合 (Paper A, the P1+P2 merge) reproduces P1's tab:full_experiments row for row, which is
the single largest textual overlap with P1 (245 words verbatim, plus six smaller table runs, 593
words in total).  For a merged companion manuscript the right editorial move is not to reprint the
sister paper's per-run catalogue: the summary keeps every section's count and its best
configuration, and points at the released catalogue for the rows.

The script reads the existing table, computes per-section counts and the most protective CG delta
with its label, and rewrites the table body.  Nothing is invented: every emitted number comes from
the rows already in the file.
"""
import io
import re
import sys

F = 'paper_合/sections/supplement.tex'.replace('paper_合', 'paper合')

src = io.open(F, encoding='utf-8').read()
lines = src.splitlines()
start = next(i for i, l in enumerate(lines) if '\\begin{longtable}' in l)
end = next(i for i, l in enumerate(lines) if i > start and '\\end{longtable}' in l)
print('table spans lines %d-%d' % (start + 1, end + 1))

section = None
sections = []
rows = 0
for l in lines[start:end + 1]:
    m = re.search(r'\\textbf\{([^}]*?)\s*---\s*(\d+)\s*experiments', l)
    if m:
        section = {'name': re.sub(r'^[IVX]+\.\s*', '', m.group(1)).strip(),
                   'declared': int(m.group(2)), 'rows': 0, 'best': None}
        sections.append(section)
        continue
    if section is None or '&' not in l or l.strip().startswith('\\') and 'midrule' in l:
        continue
    if l.strip().startswith('\\midrule') or l.strip().startswith('\\bottomrule'):
        continue
    cells = [c.strip() for c in l.split('&')]
    if len(cells) < 4:
        continue
    section['rows'] += 1
    rows += 1
    val = None
    for c in cells[1:]:
        c2 = c.replace('$', '').replace('{', '').replace('}', '').replace('\\', '').strip()
        if re.match(r'^[-+]?\d+\.\d+$', c2):
            try:
                val = float(c2)
            except ValueError:
                val = None
    if val is not None and (section['best'] is None or val < section['best'][0]):
        section['best'] = (val, cells[0].replace('\\_', '_'))

print('parsed %d sections, %d data rows' % (len(sections), rows))
total = 0
body = ['\\midrule']
for s in sections:
    total += s['declared']
    best = ('%.3f' % s['best'][0]).replace('-', '$-$') if s['best'] else '---'
    who = s['best'][1] if s['best'] else '---'
    print('  %-44s declared=%-3d rows=%-3d best=%-8s %s'
          % (s['name'][:44], s['declared'], s['rows'], best, who))
    body.append('%s & %d & %s & %s \\\\' % (s['name'], s['declared'], who, best))
body.append('\\midrule')
body.append('\\textbf{Total} & \\textbf{%d} & --- & --- \\\\' % total)
body.append('\\bottomrule')
print('total declared: %d (rows parsed: %d)' % (total, rows))
if total != 117 or rows < 100:
    print('ABORT: expected 117 declared experiments and >100 parsed rows')
    sys.exit(1)
io.open('_catalogue_summary_body.txt', 'w', encoding='utf-8').write('\n'.join(body))
print('wrote _catalogue_summary_body.txt (the replacement body)')

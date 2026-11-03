# -*- coding: utf-8 -*-
"""Catalogue count check: declared per-section experiment counts vs actual data rows.

The original 116-vs-117 bug was a section whose heading said "7 experiments" while the table
listed eight rows, so summing the headings disagreed with the total.  This tool re-derives both
numbers from the released catalogue table and reports any section where they differ, plus the
heading sum versus the printed Total.  Run it on any paper that prints an experiment catalogue.

Usage: python tools/_catalog_count_check.py paper/sections/supplementary.tex
"""
import io
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'paper/sections/supplementary.tex'
text = io.open(path, encoding='utf-8').read()

# every longtable/tabular body in the file
bodies = re.findall(r'\\begin\{(?:longtable|tabular)\}\{[^}]*\}(.*?)\\end\{(?:longtable|tabular)\}',
                    text, re.S)

total_declared = None
grand_actual = 0
for bi, body in enumerate(bodies):
    # NOTE: multicolumn section headings end with \\ but carry no '&', so do not filter on '&' here
    rows = [l.strip() for l in body.splitlines() if l.strip().endswith('\\\\')]
    sections = []
    cur = None
    for l in rows:
        s = l.strip()
        # allow a trailing superscript after the \textbf{...} group: ...}$^\ddagger$}
        head = re.search(r'\\multicolumn\{\d+\}\{[^}]*\}\{\\textbf\{([^}]*)\}[^}]*\}', s)
        if head:
            label = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?', '', head.group(1))
            label = re.sub(r'[{}]', '', label).strip()
            m = re.search(r'(\d+)\s*experiments?', label)
            cur = {'label': label, 'declared': int(m.group(1)) if m else None, 'rows': 0}
            sections.append(cur)
            continue
        if '\\midrule' in s or '\\bottomrule' in s or '\\toprule' in s:
            continue
        tot = re.search(r'\\textbf\{Total\}\s*&\s*\\textbf\{(\d+)\}', s)
        if tot:
            total_declared = int(tot.group(1))
            continue
        if '&' not in s:
            continue
        if cur is not None:
            cur['rows'] += 1
    if not sections:
        continue
    print('=== table %d in %s ===' % (bi + 1, path))
    bad = 0
    for sec in sections:
        ok = (sec['declared'] == sec['rows']) if sec['declared'] is not None else None
        flag = '' if ok else '   <-- MISMATCH'
        if ok is False:
            bad += 1
        print('  %-58s declared=%-4s rows=%-4s%s'
              % (sec['label'][:58], sec['declared'], sec['rows'], flag))
    heading_sum = sum(s['declared'] for s in sections if s['declared'] is not None)
    actual_sum = sum(s['rows'] for s in sections)
    print('  %-58s declared=%-4d rows=%-4d' % ('(sum over sections)', heading_sum, actual_sum))
    if total_declared is not None:
        print('  %-58s declared=%-4d' % ('(printed Total row)', total_declared))
        if total_declared != actual_sum:
            print('      <-- TOTAL disagrees with the actual row count (%d vs %d)'
                  % (total_declared, actual_sum))
            bad += 1
        if heading_sum != total_declared:
            print('      <-- TOTAL disagrees with the sum of the section headings (%d vs %d)'
                  % (heading_sum, total_declared))
            bad += 1
    print('  mismatches: %d' % bad)
    grand_actual += actual_sum

print('')
print('RESULT: sections sum to %d data rows; %s'
      % (grand_actual, 'no mismatch' if grand_actual else 'could not parse'))

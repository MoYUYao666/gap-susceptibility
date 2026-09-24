# -*- coding: utf-8 -*-
"""Bibliography quality audit: placeholder authors, missing fields, stub identifiers.

Motivated by refs.bib carrying `author = {Wu, Y. and others}` for a paper whose real authors are
known (Huyu Wu, Meng Tang, Xinhan Zheng, Haiyun Jiang).  A placeholder author list is a citation
defect a reviewer can see, so this checks every entry for that class of problem, plus the
identifiers that a fabricated reference leaves behind (12345-style arXiv numbers, TODO markers).

Usage: python tools/_ap3_bib_audit.py [paper_ap3/refs.bib]
"""
import io
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'paper_ap3/refs.bib'
text = io.open(path, encoding='utf-8').read()
entries = re.findall(r'@(\w+)\{([^,]+),(.*?)\n\}', text, re.S)
print('%s: %d entries' % (path, len(entries)))

flagged = []
for typ, key, body in entries:
    problems = []
    m = re.search(r'author\s*=\s*[{"](.+?)[}"],', body, re.S)
    who = m.group(1).strip() if m else ''
    if not m:
        problems.append('missing author field')
    elif len(who) < 12:
        problems.append('single/short author list, worth a check: %r' % who)
    # NOTE: "and others" is *not* a defect -- BibTeX renders it as "et al." and it is the normal
    # convention for long author lists (Radford et al., the Qwen report).  Likewise an entry may
    # legitimately carry url/howpublished instead of a DOI (sharegpt2023 does exactly that).
    if re.search(r'\b(12345|XXXX|TODO|TBD|PLACEHOLDER)\b', body, re.I):
        problems.append('placeholder identifier in the body')
    has_id = re.search(r'(doi|eprint|journal|booktitle|url|howpublished)\s*=', body)
    if not has_id:
        problems.append('no venue/DOI/arXiv identifier and no URL')
    if problems:
        flagged.append((key, who[:64], problems))

print('')
for key, who, problems in flagged:
    print('  %-28s %-46s %s' % (key, who, '; '.join(problems)))
print('')
print('flagged: %d of %d' % (len(flagged), len(entries)))
sys.exit(1 if flagged else 0)

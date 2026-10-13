"""Quick citation coverage check: bib entries vs body \\cite keys (escape issue fixed)."""
import re
import glob

bib = open('paper_ap3/refs.bib', encoding='utf-8').read()
keys = re.findall(r'^@\w+\{([^,]+),', bib, re.M)
cited = set()
for f in glob.glob('paper_ap3/sections/*.tex') + ['paper_ap3/main.tex']:
    t = open(f, encoding='utf-8').read()
    for m in re.finditer(r'\\cite\{([^}]*)\}', t):
        for k in m.group(1).split(','):
            k = k.strip()
            if k:
                cited.add(k)
print('bib entries:', len(keys))
print('cited keys :', len(cited))
unused = [k for k in keys if k not in cited]
missing = [k for k in cited if k not in keys]
print('unused     :', len(unused), unused)
print('missing    :', missing)

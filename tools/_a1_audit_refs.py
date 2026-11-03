"""Temporary audit helper: label/ref/cite inventory for paper_a1 (deleted after use)."""
import re, os, sys, collections, json

base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'paper_a1')
files = sys.argv[1:] or ['main.tex', 'related_work.tex', 'related_work_bibitems.tex',
                         'revision_additions.tex']

LAB = re.compile(r'\\label\{([^}]*)\}')
REF = re.compile(r'\\(?:ref|eqref|autoref|Cref|cref|pageref)\{([^}]*)\}')
BIB = re.compile(r'\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}')
CIT = re.compile(r'\\cite[a-zA-Z]*\{([^}]*)\}')

lab = collections.defaultdict(list)
ref = collections.defaultdict(list)
bib = collections.defaultdict(list)
cite = collections.defaultdict(list)


def strip_comments(text):
    out = []
    for ln in text.split('\n'):
        if ln.lstrip().startswith('%'):
            out.append('')
            continue
        # remove unescaped % comments
        res = []
        i = 0
        while i < len(ln):
            if ln[i] == '%' and (i == 0 or ln[i - 1] != '\\'):
                break
            res.append(ln[i])
            i += 1
        out.append(''.join(res))
    return '\n'.join(out)


for f in files:
    p = os.path.join(base, f)
    if not os.path.exists(p):
        print('MISSING FILE:', p)
        continue
    body = strip_comments(open(p, encoding='utf-8').read())
    for m in LAB.finditer(body):
        lab[m.group(1)].append(f)
    for m in REF.finditer(body):
        for k in m.group(1).split(','):
            ref[k.strip()].append(f)
    for m in BIB.finditer(body):
        bib[m.group(1)].append(f)
    for m in CIT.finditer(body):
        for k in m.group(1).split(','):
            cite[k.strip()].append(f)

print('=== LABELS (%d unique) ===' % len(lab))
for k, v in sorted(lab.items()):
    flag = '   <<< COLLISION' if len(v) > 1 else ''
    print('  %-30s %s%s' % (k, sorted(set(v)), flag))

print()
print('=== REFS (%d unique) ===' % len(ref))
unres, per_file = [], collections.defaultdict(list)
for k, v in sorted(ref.items()):
    ok = k in lab
    if not ok:
        unres.append(k)
    for f in set(v):
        per_file[f].append((k, ok))
    print('  %-30s %-11s from %s' % (k, 'OK' if ok else 'UNRESOLVED', sorted(set(v))))

print()
print('UNRESOLVED REFS:', unres)
print()
print('=== per-file ref counts ===')
for f, lst in per_file.items():
    print('  %-28s %d refs, %d unresolved' % (f, len(lst), sum(1 for _, ok in lst if not ok)))
print()

print('=== BIBITEMS: %d ===' % len(bib))
missing = [k for k in cite if k not in bib]
orphan = [k for k in bib if k not in cite]
print('CITED BUT UNDEFINED (%d): %s' % (len(missing), missing))
print('DEFINED BUT NEVER CITED (%d): %s' % (len(orphan), orphan))

"""Mechanical audit: (1) hard-coded Equation/Table/Figure/Section numbers vs. the actual numbers in .aux; (2) float/equation reference integrity."""
import re
import glob

AUX = 'paper_ap3/main.aux'
aux = open(AUX, encoding='utf-8', errors='ignore').read()
raw = re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{(\d+)\}', aux)
num_of = {k: page for k, _t, page in raw}
for k, t, _p in raw:
    if '{' not in t:
        num_of[k] = t  # for some labels the second field is the number

print('=== 1) hard-coded number references ===')
pat = re.compile(r'(Equation|Eq\.|Table|Figure|Fig\.|Section|Sec\.|Appendix|Corollary|Theorem|Lemma)\s*~?\s*\(?(\d+|[A-Z])\)?')
hits = []
for f in sorted(glob.glob('paper_ap3/sections/*.tex')) + ['paper_ap3/main.tex']:
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        for m in pat.finditer(line):
            kind, val = m.group(1), m.group(2)
            # exclude \ref forms and math symbols
            seg = line[max(0, m.start() - 12):m.start()]
            if '\\ref' in seg or '\\eqref' in seg or '\\label' in seg:
                continue
            if kind in ('Corollary', 'Theorem', 'Lemma') and val.isdigit():
                pass  # theorem numbering is checked separately
            hits.append((f.replace('paper_ap3/sections/', ''), i, kind, val, line.strip()[:110]))
for h in hits:
    print('   %-22s:%-4d %s %s | %s' % h)

print()
print('=== 2) true numbers of key labels (.aux) ===')
for lab in ['eq:allocation', 'eq:gradflow', 'eq:ode_main', 'thm:repr', 'thm:ode', 'thm:proj',
            'tab:phase', 'tab:sens', 'tab:policy', 'tab:2x2', 'tab:langonly', 'tab:alloc',
            'tab:generalization', 'tab:phase2', 'tab:layergamma', 'tab:gamma_rank',
            'fig:framework', 'fig:ode', 'fig:ers', 'fig:p3ers', 'sec:special', 'sec:crossarch',
            'sec:sens_sched', 'sec:sens_10ep', 'sec:sens_2x2', 'sec:sens_langonly', 'sec:conclusion']:
    print('   %-22s -> %s' % (lab, num_of.get(lab, 'MISSING')))

print()
print('=== 3) unreferenced labels (equations/tables/figures/theorems) ===')
tex = ''.join(open(f, encoding='utf-8').read() for f in glob.glob('paper_ap3/sections/*.tex') + ['paper_ap3/main.tex'])
all_labels = re.findall(r'\\label\{([^}]+)\}', tex)
refs = set(re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', tex))
unused = [l for l in all_labels if l not in refs]
print('   unused labels:', unused if unused else 'none')
missing = [r for r in refs if r not in all_labels]
print('   refs without label:', missing if missing else 'none')

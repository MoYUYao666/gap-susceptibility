"""Temporary: print the sectioning outline of a LaTeX fragment/body (deleted after use)."""
import re, sys

path = sys.argv[1]
t = open(path, encoding='utf-8').read()
if r'\begin{document}' in t:
    t = t.split(r'\begin{document}')[1]

pat = re.compile(r'\\(section|subsection|subsubsection)\*?\{')
level = {'section': 0, 'subsection': 1, 'subsubsection': 2}
out = []
for m in pat.finditer(t):
    end = t.index('}', m.end())
    title = t[m.end():end]
    title = re.sub(r'\\texorpdfstring\{([^}]*)\}\{[^}]*\}', r'\1', title)
    out.append((m.group(1), title))

prev = 0
for k, ti in out:
    ind = '  ' * level[k]
    flag = ''
    if level[k] > prev + 1:
        flag = '   <<< LEVEL JUMP'
    prev = level[k]
    print('%s%s %s%s' % (ind, k[0].upper(), ti, flag))

print()
counts = {k: sum(1 for a, _ in out if a == k) for k in level}
print('counts:', counts)
dup = [x for x in set(ti for _, ti in out) if [ti for _, ti in out].count(x) > 1]
print('duplicate titles:', dup)

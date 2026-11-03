import re, os

papers = [
    ('Paper 1', 'paper', 'paper/references.bib'),
    ('Paper A', 'paper合', 'paper合/references.bib'),
    ('Paper 3', 'paper3/paper_ieee', 'paper3/paper_ieee/references.bib'),
]
for label, texdir, bib in papers:
    alltex = ''
    for root, dirs, files in os.walk(texdir):
        if '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            if f.endswith('.tex'):
                alltex += open(os.path.join(root, f), encoding='utf-8', errors='ignore').read() + '\n'
    cites = set()
    for m in re.findall(r'\\cite\{([^}]+)\}', alltex):
        cites.update(c.strip() for c in m.split(','))
    bibsrc = open(bib, encoding='utf-8').read()
    keys = set(re.findall(r'@\w+\{([^,]+),', bibsrc))
    miss = cites - keys
    unused = keys - cites
    print('%-8s cites=%d bib=%d 缺失=%s 未使用=%s' % (label, len(cites), len(keys), miss or '无', unused or '无'))

# 互引检查：三篇互相引用（wan2026protect/wan2026gap）
print('\n=== 互引检查（under-review 标注）===')
for label, texdir, bib in papers:
    alltex = ''
    for root, dirs, files in os.walk(texdir):
        if '.git' in root: continue
        for f in files:
            if f.endswith('.tex'):
                alltex += open(os.path.join(root, f), encoding='utf-8', errors='ignore').read() + '\n'
    for k in ['wan2026protect', 'wan2026gap']:
        n = alltex.count('\\cite{%s}' % k) + alltex.count('\\citep{%s}' % k) + alltex.count('\\citet{%s}' % k)
        if n:
            bibsrc = open(bib, encoding='utf-8').read()
            entry = re.search(r'@\w+\{%s,([^@]*?)\n\}' % k, bibsrc, re.S)
            note = 'under review' if entry and 'under review' in entry.group(1).lower() else ('无标注!' if entry else 'bib 缺失!')
            print('%-8s 引用 %-14s %d 次 | %s' % (label, k, n, note))

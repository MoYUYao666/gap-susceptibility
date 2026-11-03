import re, os
for root, dirs, files in os.walk('paper合'):
    if '.git' in root: continue
    for f in files:
        if f.endswith('.tex'):
            p = os.path.join(root, f)
            src = open(p, encoding='utf-8', errors='ignore').read()
            for m in re.finditer(r'\\cite\{([^}]+)\}', src):
                keys = [k.strip() for k in m.group(1).split(',')]
                if any(k.startswith('bib') for k in keys):
                    print('%s: %s' % (p, m.group(0)[:70]))

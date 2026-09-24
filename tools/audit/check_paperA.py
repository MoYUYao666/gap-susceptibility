import re, os
alltex = open('paper合/main_springer.tex', encoding='utf-8', errors='ignore').read()
for f in os.listdir('paper合/sections'):
    if f.endswith('.tex'):
        alltex += open(os.path.join('paper合/sections', f), encoding='utf-8', errors='ignore').read() + '\n'
cites = set()
for m in re.findall(r'\\cite\{([^}]+)\}', alltex):
    cites.update(c.strip() for c in m.split(','))
bibsrc = open('paper合/references.bib', encoding='utf-8').read()
keys = set(re.findall(r'@\w+\{([^,]+),', bibsrc))
print('Paper A 正文: cites=%d bib=%d 缺失=%s 未使用=%s' % (len(cites), len(keys), cites-keys or '无', keys-cites or '无'))
for k in ['kang2025dmnsp', 'wang2026violet']:
    if k in alltex or k in bibsrc:
        print('!! 残留:', k)
print('fake 残留检查完成')

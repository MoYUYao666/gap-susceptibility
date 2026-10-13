import re, os

alltex = ''
for f in ['main_springer.tex'] + ['sections/%s' % f for f in os.listdir('sections') if f.endswith('.tex')]:
    alltex += open(f, encoding='utf-8').read() + '\n'

cites = set()
for m in re.findall(r'\\cite\{([^}]+)\}', alltex):
    cites.update(c.strip() for c in m.split(','))
bib = open('references.bib', encoding='utf-8').read()
keys = set(re.findall(r'@\w+\{([^,]+),', bib))
unused = keys - cites
print('Unused entries:', unused if unused else 'none')
entries = re.split(r'(?=@\w+\{)', bib)
kept = [e for e in entries if not (e.startswith('@') and re.match(r'@\w+\{(%s),' % '|'.join(unused), e))]
open('references.bib', 'w', encoding='utf-8').write(''.join(kept))
keys2 = set(re.findall(r'@\w+\{([^,]+),', open('references.bib').read()))
print('bib entries:', len(keys2), '| removed:', len(unused))

"""A23（paper_a2，A2+A3 合并稿）状态盘点：词数、浮动体、结构、待修项。"""
import os
import re
import glob

ROOT = 'paper_a2'


def strip_tex(txt):
    """去掉注释与常见非正文环境，给出近似正文词数。"""
    txt = re.sub(r'(?m)^\s*%.*$', '', txt)
    txt = re.sub(r'\\begin\{(table|figure|tabular|longtable)\*?\}.*?\\end\{\1\*?\}',
                 ' ', txt, flags=re.S)
    txt = re.sub(r'\$[^$]*\$', ' ', txt)
    txt = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', txt)
    return txt


def count_words(path):
    txt = open(path, encoding='utf-8').read()
    body = strip_tex(txt)
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", body))


files = sorted(glob.glob(os.path.join(ROOT, '*.tex')))
print('=== paper_a2 下的 .tex ===')
tot_en = 0
for f in files:
    base = os.path.basename(f)
    txt = open(f, encoding='utf-8').read()
    w = count_words(f)
    is_en = not base.startswith('zh_') and '_zh' not in base
    tag = 'EN' if is_en else 'ZH'
    if is_en:
        tot_en += w
    print('  %-34s %8d B  %6d 词  [%s]' % (base, len(txt), w, tag))

main_en = os.path.join(ROOT, 'main.tex')
txt = open(main_en, encoding='utf-8').read()
inputs = re.findall(r'\\input\{([^}]+)\}', txt)
print()
print('=== main.tex 结构 ===')
print('  \\input:', inputs)
print('  \\section      =', len(re.findall(r'\\section\{', txt)))
print('  \\subsection   =', len(re.findall(r'\\subsection\{', txt)))
print('  table 环境    =', len(re.findall(r'\\begin\{table', txt)))
print('  figure 环境   =', len(re.findall(r'\\begin\{figure', txt)))
print('  \\cite 次数   =', len(re.findall(r'\\cite\{', txt)))
print('  \\ref 次数    =', len(re.findall(r'\\ref\{', txt)))
labels = re.findall(r'\\label\{([^}]+)\}', txt)
print('  \\label 个数  =', len(labels))
refs = set(re.findall(r'\\ref\{([^}]+)\}', txt))
unref = [l for l in labels if l not in refs]
print('  定义了但没被 \\ref 的 label:', unref if unref else '无')

print()
print('=== main.tex + \\input 的英文正文词数（近似）===')
parts = [main_en] + [os.path.join(ROOT, i + '.tex') for i in inputs]
parts = [p for p in parts if os.path.exists(p)]
tot = sum(count_words(p) for p in parts)
print('  合计 = %d 词（含 ext 分部）' % tot)
print('  仅 main.tex = %d 词' % count_words(main_en))

for p in sorted(glob.glob(os.path.join(ROOT, 'ext_*.tex'))):
    print('    %-34s %6d 词' % (os.path.basename(p), count_words(p)))

print()
print('=== 交付物清单 ===')
for pat in ('*.pdf', '*.tex', '*.md', '*.docx', '*.doc', 'figures/*'):
    got = sorted(glob.glob(os.path.join(ROOT, pat)))
    if got:
        print('  %-12s %d 个' % (pat, len(got)))
        for g in got[:30]:
            print('      %-40s %8d B' % (os.path.relpath(g, ROOT), os.path.getsize(g)))

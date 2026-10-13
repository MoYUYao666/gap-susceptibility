"""A23 补充盘点：词数口径、引用数、未被引用的浮动体、cover letter 刊名、EI 指南是否在库。"""
import os
import re
import glob

en = ['paper_a2/main.tex'] + sorted(glob.glob('paper_a2/ext_*.tex'))
raw = prose = cites = 0
for f in en:
    t = open(f, encoding='utf-8').read()
    t2 = re.sub(r'(?m)^\s*%.*$', '', t)
    raw += len(re.findall(r"[A-Za-z][A-Za-z'\-]*", t2))
    b = re.sub(r'\\begin\{(table|figure|tabular|longtable)\*?\}.*?\\end\{\1\*?\}',
               ' ', t2, flags=re.S)
    b = re.sub(r'\$[^$]*\$', ' ', b)
    b = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', b)
    prose += len(re.findall(r"[A-Za-z][A-Za-z'\-]*", b))
    cites += len(re.findall(r'\\cite\{', t2))

print('EN 散文词数（剔除表格/图/公式） = %d' % prose)
print('EN 全部字母词（含表格/图注/公式） = %d' % raw)
print('EN \\cite 命令总数                = %d' % cites)

allrefs = set()
labels = []
for f in en:
    t = open(f, encoding='utf-8').read()
    allrefs |= set(re.findall(r'\\ref\{([^}]+)\}', t))
    for lb in re.findall(r'\\label\{([^}]+)\}', t):
        if lb.startswith(('fig:', 'tab:', 'thm:', 'eq:')):
            labels.append(lb)
print('浮动体/定理 label 总数 = %d；从未被 \\ref 的 = %s'
      % (len(labels), [l for l in labels if l not in allrefs]))

cl = open('paper_a2/cover_letter.tex', encoding='utf-8').read()
names = set(re.findall(r'(Ocean Engineering|Ecological Informatics|Neurocomputing|'
                       r'Pattern Recognition Letters|Multimedia Tools and Applications)',
                       cl))
print('cover_letter 中出现的刊名 = %s' % (names or '（未识别到刊名关键字）'))

hits = [os.path.relpath(p) for p in
        glob.glob('**/*Ecological*', recursive=True)][:8]
print('库内 Ecological Informatics 相关文件 = %s' % (hits or '无'))
gi = [os.path.relpath(p) for p in glob.glob('**/*Guide*author*', recursive=True)][:8]
print('库内 Guide for authors 文件 = %s' % gi)

print()
print('=== 待修项自检 ===')
mt = open('paper_a2/main.tex', encoding='utf-8').read()
zh = open('paper_a2/main_zh.tex', encoding='utf-8').read()
checks = [
    ('EN 声明性段落 Declaration of competing interest',
     'competing interest' in mt.lower() or 'conflict of interest' in mt.lower()),
    ('EN CRediT 作者贡献', 'credit' in mt.lower()),
    ('EN 数据可得性段', 'data availability' in mt.lower()),
    ('EN 生成式 AI 披露', 'generative ai' in mt.lower() or 'large language model' in mt.lower()),
    ('EN 性别/性别相关限制句', 'sex' in mt.lower() or 'gender' in mt.lower()),
    ('EN 与 PRL/PR 的重复投稿披露', 'PRLETTERS-D-26-01941' in mt),
    ('ZH 与 PRL/PR 的重复投稿披露', 'PRLETTERS-D-26-01941' in zh),
    ('ZH 中 fig:sonar-sigma 是否被引用', 'ref{fig:sonar-sigma}' in zh),
]
for name, ok in checks:
    print('  [%s] %s' % ('有' if ok else '缺', name))

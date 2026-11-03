"""A23 逐节词数盘点：定位 main.tex 的 section / input 结构，给压缩预算。"""
import os
import re

ROOT = 'paper_a2'
MAIN = os.path.join(ROOT, 'main.tex')
raw = open(MAIN, encoding='utf-8').read()
lines = raw.split('\n')


def count(text):
    """近似正文词数：去注释、公式、表/图环境与命令。"""
    text = re.sub(r'(?m)^\s*%.*$', '', text)
    text = re.sub(r'\\begin\{(table|figure|tabular|longtable)\*?\}.*?\\end\{\1\*?\}',
                  ' ', text, flags=re.S)
    text = re.sub(r'\$[^$]*\$', ' ', text)
    text = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', text)
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


marks = []
for i, ln in enumerate(lines):
    m = re.match(r'\s*\\(section|input|appendix|begin\{thebibliography)\*?\s*[{(]?([^}]*)\}?', ln)
    if m:
        kind = m.group(1)
        arg = m.group(2).strip()
        if kind == 'section' or kind == 'input' or kind == 'appendix' or 'thebibliography' in kind:
            marks.append((i, kind, arg))

print('=== main.tex 结构标记 ===')
for i, kind, arg in marks:
    print('  行 %5d  %-20s %s' % (i + 1, kind, arg))

print()
print('=== 按 section 切分的词数（不含 \\input 展开）===')
tot = 0
for idx, (i, kind, arg) in enumerate(marks):
    if kind != 'section':
        continue
    j = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
    w = count('\n'.join(lines[i:j]))
    tot += w
    print('  %-42s %6d 词   行 %d-%d' % (arg[:42], w, i + 1, j))
print('  %-42s %6d 词' % ('[main.tex 全部 section 合计]', tot))

print()
print('=== \\input 分部逐节 ===')
for name in re.findall(r'\\input\{([^}]+)\}', raw):
    p = os.path.join(ROOT, name + '.tex')
    if not os.path.exists(p):
        print('  %s 缺失' % p)
        continue
    t = open(p, encoding='utf-8').read()
    subs = re.findall(r'\\(section|subsection)\{([^}]*)\}', t)
    print('  %s : 合计 %d 词' % (name, count(t)))
    for k, a in subs:
        print('        %-10s %s' % (k, a[:60]))

print()
print('=== 表/图所在位置与规模 ===')
for i, ln in enumerate(lines):
    m = re.search(r'\\begin\{(table|figure)\*?\}', ln)
    if m:
        j = i
        while j < len(lines) and ('\\end{%s' % m.group(1)) not in lines[j]:
            j += 1
        block = '\n'.join(lines[i:j + 1])
        cap = re.search(r'\\caption\{(.{0,70})', block, flags=re.S)
        lab = re.search(r'\\label\{([^}]+)\}', block)
        print('  %-8s 行 %5d-%5d  %5d B  %-22s %s'
              % (m.group(1), i + 1, j + 1, len(block),
                 (lab.group(1) if lab else '-'),
                 (cap.group(1).replace('\n', ' ') if cap else '')))

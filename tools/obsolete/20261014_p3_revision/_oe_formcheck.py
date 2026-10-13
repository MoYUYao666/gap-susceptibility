"""OE 形式要求自检：摘要 ≤200 词、关键词 1-7 个、Highlights 3-5 条且每条 ≤85 字符。"""
import os
import re


def render(tex):
    """把 LaTeX 大致还原成排版后的纯文本，用于按"排版后字符数"计数。"""
    s = tex
    s = re.sub(r'\\emph\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\textit\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\textbf\{([^}]*)\}', r'\1', s)
    s = s.replace('\\times', 'x').replace('\\%', '%').replace('\\,', ' ')
    s = s.replace('$', '').replace('{', '').replace('}', '')
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


main = open('paper_a2/main.tex', encoding='utf-8').read()

# --- 摘要 ---
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', main, flags=re.S)
abs_tex = m.group(1)
abs_txt = render(abs_tex)
print('=== 摘要 ===')
print('  排版后词数 = %d   (OE 要求 <= 200)' % len(abs_txt.split()))
print('  超限 %d 词' % max(0, len(abs_txt.split()) - 200))
if len(abs_txt.split()) > 200:
    sents = re.split(r'(?<=[.;])\s+', abs_txt)
    print('  句子数 = %d，各句词数: %s' % (len(sents), [len(x.split()) for x in sents]))
    print('  最长三句:')
    for x in sorted(sents, key=lambda t: -len(t.split()))[:3]:
        print('    [%3d 词] %s' % (len(x.split()), x[:150]))
print('  含引用/公式: %s' % ('是' if ('\\cite' in abs_tex or '$' in abs_tex) else '否'))

# --- 关键词 ---
m = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', main, flags=re.S)
kws = [k.strip() for k in re.split(r'\\sep', m.group(1)) if k.strip()]
print()
print('=== 关键词 ===')
print('  个数 = %d  (OE 要求 1-7)' % len(kws))
for k in kws:
    print('    -', k)

# --- Highlights ---
print()
print('=== Highlights ===')
ht = open('paper_a2/highlights.tex', encoding='utf-8').read()
items = re.findall(r'\\item\s+(.*?)(?=\n\\item|\n\\end\{itemize\})', ht, flags=re.S)
print('  条数 = %d  (OE 要求 3-5)' % len(items))
bad = 0
for i, it in enumerate(items, 1):
    one = ' '.join(it.split())
    r = render(one)
    flag = 'OK ' if len(r) <= 85 else '超限'
    if len(r) > 85:
        bad += 1
    print('  %d. [%s %3d 字符] %s' % (i, flag, len(r), r))
print('  超限条数 = %d' % bad)

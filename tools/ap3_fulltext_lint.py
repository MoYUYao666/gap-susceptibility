"""paper_ap3 全文内容级体检（补编译审计抓不到的那一类缺陷）。

检查项：
  A 残留伪影：Python 源码残片(r'...' 开头)、TODO/FIXME/占位符、`??`、空的 \\ref{}/\\cite{}、
    行尾孤立的 `: '`、未闭合的 `` 引号对
  B 重复段落/句子：规范化后长度 >= 70 字符的句子出现 >= 2 次
  C 局限编号：limitations 段里的序数词顺序 vs 全文 `Limitation~N` 引用是否越界
  D 数字溯源：正文里出现的数字（含 $..$ 内）是否能在 outputs/*.json 与
    paper3/scripts/outputs/experiments/*.json 中找到出处；列出找不到的候选
  E 浮动体与引用：每个 table/figure 是否被 \\ref 引用；每个 \\ref 是否都能在 \\label 中找到

用法： python tools/ap3_fulltext_lint.py [paper_ap3]
退出码：0 = 无 A/C/E 级问题（B/D 为提示性）
"""
import glob
import json
import os
import re
import sys
from collections import Counter

# 2026-09-20: argv[1] used to be taken as the paper directory whatever it was, so passing a flag
# (e.g. --all) made the glob match nothing and every check pass vacuously -- a false PASS.  Options
# are now separated from the positional directory, and an empty file set aborts instead.
_args = [a for a in sys.argv[1:] if not a.startswith('--')]
SHOW_ALL = '--all' in sys.argv
DIR = _args[0] if _args else 'paper_ap3'
TEX = sorted(glob.glob(os.path.join(DIR, '*.tex')) + glob.glob(os.path.join(DIR, 'sections', '*.tex')))
if not TEX:
    print('ABORT: no .tex files found under %r — refusing to report a vacuous PASS' % DIR)
    sys.exit(2)
ORDINALS = ['First,', 'Second,', 'Third,', 'Fourth,', 'Fifth,', 'Sixth,', 'Seventh,', 'Eighth,',
            'Ninth,', 'Tenth,', 'Eleventh,', 'Twelfth,', 'Thirteenth,', 'Fourteenth,',
            'Fifteenth,', 'Sixteenth,', 'Seventeenth,']
WORD2NUM = {w: i + 1 for i, w in enumerate(ORDINALS)}

problems = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}

# ---------- 读取 ----------
files = {}
for p in TEX:
    files[p] = open(p, encoding='utf-8', errors='replace').read()


def lines_of(txt):
    return txt.splitlines()


# ---------- A 残留伪影 ----------
PAT_ARTIFACT = [
    (re.compile(r"^\s*r'"), 'Python 原始字符串残片'),
    (re.compile(r'^\s*(import |from \w+ import|def |class |print\(|json\.dump|torch\.)'), 'Python 源码行'),
    (re.compile(r'\b(TODO|FIXME|XXX|TBD|PLACEHOLDER|待补|待填|WIP)\b'), '占位符标记'),
    (re.compile(r'\?\?'), '未解析引用标记 ??'),
    (re.compile(r'\\ref\{\s*\}'), '空的 \\ref{}'),
    (re.compile(r'\\cite\{\s*\}'), '空的 \\cite{}'),
    (re.compile(r":\s*'\s*$"), '行尾孤立的引号残片'),
    (re.compile(r'```'), 'Markdown 代码围栏'),
    (re.compile(r'\\begin\{tabular\}.*\\end\{tabular\}.*\\end\{tabular\}'), '重复的 tabular 结束'),
]
for p, txt in files.items():
    for i, ln in enumerate(lines_of(txt), 1):
        for rx, why in PAT_ARTIFACT:
            if rx.search(ln):
                problems['A'].append(f'{os.path.relpath(p, DIR)}:{i}  [{why}]  {ln.strip()[:110]}')

# ---------- B 重复句 ----------
sent_counter = Counter()
sent_where = {}
for p, txt in files.items():
    flat = re.sub(r'\s+', ' ', txt)
    for m in re.finditer(r'[^.!?]{70,}?[.!?]', flat):
        s = m.group(0).strip()
        s = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', 'X', s)      # 去掉 \ref{} 之类
        s = re.sub(r'\s+', ' ', s)
        sent_counter[s] += 1
        sent_where.setdefault(s, []).append(os.path.relpath(p, DIR))
for s, c in sent_counter.items():
    if c >= 2:
        problems['B'].append(f'出现 {c} 次于 {sorted(set(sent_where[s]))}: {s[:130]}')

# ---------- C 局限编号 ----------
lim_txt = files.get(os.path.join(DIR, 'sections', '07_discussion.tex'), '')
found = [(m.start(), w) for w in ORDINALS for m in re.finditer(re.escape(w), lim_txt)]
found.sort()
order = [w for _, w in found]
nums = [WORD2NUM[w] for w in order]
if nums != sorted(nums):
    problems['C'].append(f'序数词出现顺序不单调: {order}')
gaps = [n for n in range(1, max(nums) + 1) if n not in nums] if nums else []
if gaps:
    problems['C'].append(f'序数词缺号（未出现的局限编号）: {gaps}')
maxlim = max(nums) if nums else 0
refs = set()
for p, txt in files.items():
    for m in re.finditer(r'Limitation~?(\d+)', txt):
        refs.add(int(m.group(1)))
    for m in re.finditer(r'Limitation[s]?~?(\d+)', txt):
        refs.add(int(m.group(1)))
over = sorted(r for r in refs if r > maxlim)
if over:
    problems['C'].append(f'引用了不存在的局限编号: {over}（实际最多 {maxlim}）')
missing_refs = sorted(set(range(1, maxlim + 1)) - refs)
print(f'  [C] limitations 段共 {maxlim} 条；被 \\ref 提到过的编号: {sorted(refs)}')
if missing_refs:
    print(f'      （从未被引用的编号，仅提示: {missing_refs}）')

# ---------- D 数字溯源 ----------
# 2026-09-20: the source glob was `outputs/*.json` (non-recursive), so every nested archive —
# including outputs/theory/siglip/, outputs/siglip/ and outputs/analysis/, i.e. exactly the files
# behind the SigLIP claims — was invisible and its numbers were reported as untraceable.  It is now
# recursive, and the rounding variants reach four decimals because the manuscript quotes up to four.
data_tokens = set()
num_files = 0
for pat in ('outputs/**/*.json', 'paper3/scripts/outputs/**/*.json',
            'paper3/scripts/outputs/**/*.log'):
    for p in glob.glob(pat, recursive=True):
        num_files += 1
        try:
            txt = open(p, encoding='utf-8', errors='replace').read()
        except Exception:  # noqa: BLE001
            continue
        for m in re.finditer(r'-?\d+\.?\d*', txt):
            t = m.group(0)
            data_tokens.add(t)
            try:
                f = float(t)
                data_tokens.add(f'{f:.0f}')
                data_tokens.add(f'{f:.1f}')
                data_tokens.add(f'{abs(f):.0f}')
                if f != 0:
                    data_tokens.add(f'{abs(f):.2f}')
                    data_tokens.add(f'{abs(f):.3f}')
                    data_tokens.add(f'{abs(f):.4f}')
            except ValueError:
                pass

SKIP = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '100', '1000',
        '2024', '2025', '2026', '16', '20', '24', '32', '64', '128', '256',
        # documentation facts rather than measurements (and split by the thousands comma anyway)
        '52002', '002'}
suspicious = []
for p, txt in files.items():
    if 'sections' not in p and os.path.basename(p) == 'main.tex':
        continue
    if 'cover_letter' in os.path.basename(p):
        continue  # disclosure text: manuscript numbers, dates and journal IDs, not measurements
    for m in re.finditer(r'(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])', txt):
        tok = m.group(1)
        if tok in SKIP or tok in data_tokens:
            continue
        ctx = txt[max(0, m.start() - 60):m.end() + 40].replace('\n', ' ')
        suspicious.append((tok, os.path.relpath(p, DIR), ctx.strip()[:120]))
# 只列出出现 >=3 次或长度>=3 的（单次小数字多半是枚举/页码）
# 2026-09-20: the list used to be truncated here with [:40], and the report printed that truncated
# length, so "40 candidates" was a saturated cap rather than a count and real improvements were
# invisible.  Keep the full list; the printer slices for display.
cnt = Counter(t for t, _, _ in suspicious)
problems['D'] = [f'{t}  (×{cnt[t]})  … {c}' for t, f, c in suspicious if cnt[t] >= 3 or len(t) >= 3]
print(f'  [D] 数据文件 {num_files} 个，提取数字 token {len(data_tokens)} 个；'
      f'正文中找不到出处的数字候选 {len(problems["D"])} 条（提示性，需人工判断）')

# ---------- E 浮动体与引用 ----------
labels = set()
for p, txt in files.items():
    labels |= set(re.findall(r'\\label\{([^}]+)\}', txt))
refs_all = set()
for p, txt in files.items():
    refs_all |= set(re.findall(r'\\ref\{([^}]+)\}', txt))
floats = {}
for p, txt in files.items():
    for m in re.finditer(r'\\begin\{(table|figure)\}', txt):
        seg = txt[m.start():m.start() + 4000]
        lm = re.search(r'\\label\{([^}]+)\}', seg)
        if lm:
            floats[lm.group(1)] = (m.group(1), os.path.relpath(p, DIR))
unref = sorted(k for k in floats if k not in refs_all)
if unref:
    problems['E'].append(f'未被引用的浮动体: {[(k, floats[k][1]) for k in unref]}')
dangling = sorted(r for r in refs_all if r not in labels)
if dangling:
    problems['E'].append(f'\\ref 指向不存在的 label: {dangling}')

# ---------- 输出 ----------
print()
for k in 'ABCE':
    print(f'=== 检查 {k}：{len(problems[k])} 条 ===')
    for item in problems[k][:25]:
        print('   -', item)
    print()
print(f'=== 检查 D（数字溯源候选，提示性）：{len(problems["D"])} 条 ===')
# 默认只显示前 15 条；`--all` 输出完整清单，便于逐条人工分类（派生量 / 文档性数字 / 真无出处）
for item in (problems['D'] if SHOW_ALL else problems['D'][:15]):
    print('   -', item)

print()
hard = len(problems['A']) + len(problems['C']) + len(problems['E'])
print(f'判定：A/C/E 级问题合计 {hard} 条 → {"PASS" if hard == 0 else "NEEDS REVIEW"}；'
      f'B 重复句 {len(problems["B"])} 条、D 待核数字 {len(problems["D"])} 条（提示性）')
sys.exit(0 if hard == 0 else 1)

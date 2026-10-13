"""A23 表格数字溯源 v2：为每张表找出【最可能的来源 JSON】，并给出覆盖率。

v1 的做法（在整个 JSON 语料里找"是否有这个数"）不构成证据——十几万个叶子数值里
几乎任何 3 位小数都会碰巧命中。v2 改为：对每张表，统计每个 JSON 文件覆盖了它多少
个数字，按覆盖率排序。覆盖率显著领先的文件才可能是真实来源；若全都很低，说明该表
的数字是派生量（比值/均值），需要人工按语义回溯。
"""
import os
import re
import json
import glob
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--json-root', default='outputs')
ap.add_argument('--extra-root', default='paper3/scripts/outputs')
ap.add_argument('--exclude', default='_archive')
ap.add_argument('--min-cover', type=float, default=0.0)
args = ap.parse_args()

TEX = ['paper_a2/main.tex'] + sorted(glob.glob('paper_a2/ext_*.tex'))


def extract_tables(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'\\begin\{(table|longtable)\*?\}(.*?)\\end\{\1\*?\}', txt, flags=re.S):
        block = m.group(2)
        lab = re.search(r'\\label\{([^}]+)\}', block)
        out.append((os.path.basename(path), lab.group(1) if lab else '(no-label)', block))
    return out


def numbers_in(block):
    b = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', block)
    b = b.replace('{,}', '')
    vals = set()
    for t in re.findall(r'-?\d+\.\d+', b):
        v = float(t)
        if abs(v) >= 0.005:
            vals.add(round(v, 4))
    return vals


def walk(obj, path, sink):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, '%s.%s' % (path, k), sink)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, '%s[%d]' % (path, i), sink)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        sink.add(round(float(obj), 4))
    elif isinstance(obj, str):
        for t in re.findall(r'-?\d+\.\d+', obj):
            sink.add(round(float(t), 4))


files = sorted(glob.glob(os.path.join(args.json_root, '**', '*.json'), recursive=True))
if args.extra_root:
    files += sorted(glob.glob(os.path.join(args.extra_root, '**', '*.json'), recursive=True))
files = [f for f in files if args.exclude not in f]
print('纳入的结果 JSON 文件数 = %d（已排除含 "%s" 的路径）' % (len(files), args.exclude))

corpus = {}
for f in files:
    s = set()
    try:
        walk(json.load(open(f, encoding='utf-8')), '', s)
    except Exception:
        continue
    if s:
        corpus[os.path.relpath(f).replace('\\', '/')] = s
print('有效文件 %d 个' % len(corpus))

tables = []
for t in TEX:
    tables += extract_tables(t)

print()
for src, lab, block in tables:
    vals = numbers_in(block)
    if not vals:
        continue
    scored = []
    for f, s in corpus.items():
        hit = len(vals & s)
        if hit:
            scored.append((hit / len(vals), hit, f))
    scored.sort(reverse=True)
    print('=== %-18s (%s)  数字 %d 个' % (lab, src, len(vals)))
    if not scored:
        print('    没有任何 JSON 覆盖 → 纯派生量，需人工语义回溯')
        continue
    for cov, hit, f in scored[:3]:
        print('    %5.1f%%  (%2d/%d)  %s' % (cov * 100, hit, len(vals), f))
    if scored[0][0] < 0.5:
        print('    ⚠ 最高覆盖不足 50% → 该表数字多为派生量或跨实验拼接，需人工核')
    print()

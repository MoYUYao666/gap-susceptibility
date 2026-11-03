"""A23 表格数字溯源 v3：IDF 加权找来源。

v2 的覆盖率被"大文件"污染——a1_margins.json 有数千个逐样本叶子数值，几乎任何表
都能被它碰巧覆盖 50%+。v3 给每个数字按稀有度加权：df(v)=含该值的文件数，
weight=ln(N/(1+df))。只有包含**稀有且特定**数值的文件才会得高分。
"""
import os
import re
import json
import glob
import math
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--json-root', default='outputs')
ap.add_argument('--extra-root', default='paper3/scripts/outputs')
ap.add_argument('--exclude', default='_archive')
args = ap.parse_args()

TEX = ['paper_a2/main.tex'] + sorted(glob.glob('paper_a2/ext_*.tex'))


def extract_tables(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'\\begin\{(table|longtable)\*?\}(.*?)\\end\{\1\*?\}', txt, flags=re.S):
        lab = re.search(r'\\label\{([^}]+)\}', m.group(2))
        out.append((os.path.basename(path), lab.group(1) if lab else '(no-label)', m.group(2)))
    return out


def numbers_in(block):
    b = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', block).replace('{,}', '')
    return {round(float(t), 4) for t in re.findall(r'-?\d+\.\d+', b) if abs(float(t)) >= 0.005}


def walk(obj, sink):
    if isinstance(obj, dict):
        for v in obj.values():
            walk(v, sink)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, sink)
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

corpus = {}
for f in files:
    s = set()
    try:
        walk(json.load(open(f, encoding='utf-8')), s)
    except Exception:
        continue
    if s:
        corpus[os.path.relpath(f).replace('\\', '/')] = s
N = len(corpus)
print('有效结果 JSON = %d 个' % N)

tables = []
for t in TEX:
    tables += extract_tables(t)

all_tab_nums = set()
for _, _, b in tables:
    all_tab_nums |= numbers_in(b)

df = {v: sum(1 for s in corpus.values() if v in s) for v in all_tab_nums}
print('表内不同数值 = %d 个；其中在全语料里唯一出现的 = %d 个'
      % (len(all_tab_nums), sum(1 for v in all_tab_nums if df[v] == 1)))

print()
for src, lab, block in tables:
    vals = numbers_in(block)
    if not vals:
        continue
    w = {v: math.log(N / (1.0 + df[v])) for v in vals}
    tot_w = sum(w.values())
    scored = []
    for f, s in corpus.items():
        hit = vals & s
        if hit:
            sw = sum(w[v] for v in hit)
            scored.append((sw / tot_w, len(hit), len(vals), sw, f))
    scored.sort(reverse=True)
    print('=== %-18s (%s)  数字 %d 个，加权总量 %.2f' % (lab, src, len(vals), tot_w))
    if not scored:
        print('    无任何覆盖 → 纯派生量')
    for wc, hit, nv, sw, f in scored[:3]:
        print('    IDF 覆盖 %5.1f%%  (%2d/%d 个, 权重 %.2f)  %s' % (wc * 100, hit, nv, sw, f))
    top = scored[0][0] if scored else 0
    if top < 0.30:
        print('    ⚠ 最高 IDF 覆盖 <30%% → 数字多为派生量或跨实验拼接，须人工语义回溯')
    elif scored[0][4].endswith('a1_margins.json') and top < 0.6:
        print('    ⚠ 头名仍是逐样本大文件，可能仍是巧合 → 人工确认')
    print()

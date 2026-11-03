"""A23 表格数字溯源：把 16 张表（含附录表）里的数字逐个回到 outputs/ 的 JSON 里找。

思路：抽取表内所有 2 位以上小数的数字 → 在全部结果 JSON 的叶子数值里找匹配
      （同时试 f 与 f*100，兼容"存的是比例、印的是百分数"）。
输出：每个数字命中的 JSON 文件与键路径；找不到的单独列出待人工核。
用法：python tools/_a23_number_trace.py [--json-root outputs]
"""
import os
import re
import sys
import json
import glob
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--json-root', default='outputs')
ap.add_argument('--extra-root', default='paper3/scripts/outputs')
ap.add_argument('--tol', type=float, default=0.0051)
args = ap.parse_args()

TEX = ['paper_a2/main.tex'] + sorted(glob.glob('paper_a2/ext_*.tex'))


def extract_tables(path):
    txt = open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'\\begin\{(table|longtable)\*?\}(.*?)\\end\{\1\*?\}', txt, flags=re.S):
        block = m.group(2)
        lab = re.search(r'\\label\{([^}]+)\}', block)
        cap = re.search(r'\\caption\{(.{0,90})', block, flags=re.S)
        out.append((path, lab.group(1) if lab else '(no-label)',
                    (cap.group(1).replace('\n', ' ') if cap else '')[:90], block))
    return out


def numbers_in(block):
    b = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', block)
    b = b.replace('{,}', '')
    vals = set()
    for t in re.findall(r'-?\d+\.\d+', b):
        v = float(t)
        if abs(v) >= 0.005:
            vals.add(round(v, 4))
    return sorted(vals)


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
        sink.append((float(obj), path))
    elif isinstance(obj, str):
        for t in re.findall(r'-?\d+\.\d+', obj):
            sink.append((float(t), path + ':str'))


files = sorted(glob.glob(os.path.join(args.json_root, '**', '*.json'), recursive=True))
if args.extra_root:
    files += sorted(glob.glob(os.path.join(args.extra_root, '**', '*.json'), recursive=True))
print('结果 JSON 文件数 = %d' % len(files))

corpus = []
for f in files:
    try:
        walk(json.load(open(f, encoding='utf-8')), os.path.relpath(f).replace('\\', '/'), corpus)
    except Exception:
        continue
print('叶子数值总数 = %d' % len(corpus))

# 建索引：按 4 位小数与 2 位小数分桶
idx4, idx2 = {}, {}
for v, p in corpus:
    idx4.setdefault(round(v, 4), []).append(p)
    idx2.setdefault(round(v, 2), []).append(p)


def find(v):
    hits = idx4.get(round(v, 4), [])
    if not hits:
        hits = idx2.get(round(v, 2), [])
    # 百分比/比例互换
    if not hits:
        for alt in (v / 100.0, v * 100.0):
            hits = idx4.get(round(alt, 4), []) or idx2.get(round(alt, 2), [])
            if hits:
                hits = ['(x100/100) ' + h for h in hits]
                break
    return hits


tables = []
for t in TEX:
    tables += extract_tables(t)

print()
print('=== 表格清单（%d 张）===' % len(tables))
total = miss = 0
missing_report = []
for path, lab, cap, block in tables:
    vals = numbers_in(block)
    found, notfound = [], []
    for v in vals:
        h = find(v)
        total += 1
        if h:
            found.append((v, h[0]))
        else:
            notfound.append(v)
            miss += 1
    print()
    print('--- %s  [%s]' % (lab, os.path.basename(path)))
    print('    caption: %s' % cap)
    print('    数字 %d 个，命中 %d，未命中 %d' % (len(vals), len(found), len(notfound)))
    if notfound:
        print('    ⚠ 未在 JSON 中直接找到: %s' % notfound)
        missing_report.append((lab, notfound))
    for v, src in found[:6]:
        print('      %-10s <- %s' % (v, src))

print()
print('=== 合计：%d 个数字，未命中 %d 个（%.1f%%）===' % (total, miss, 100.0 * miss / max(total, 1)))
if missing_report:
    print()
    print('=== 需人工核对的表 ===')
    for lab, nf in missing_report:
        print('  %-22s %s' % (lab, nf))

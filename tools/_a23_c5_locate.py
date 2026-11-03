"""C5 定位：tab:theory-stack 的"9/9 ≤0.002"到底出自哪个键？0.0624 又出自哪个键？"""
import json
import glob

FILES = ['outputs/a1_tau_holdout.json', 'outputs/a1_theory_verify.json']


def walk(o, p, out):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, '%s.%s' % (p, k), out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, '%s[%d]' % (p, i), out)
    elif isinstance(o, float):
        out.append((o, p))


data = {}
for f in FILES:
    try:
        data[f] = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print('%s 读取失败 %s' % (f, e))

print('=== 1) 谁提供 n=9 且 max|diff| = 0.0019 ===')
for f, d in data.items():
    tv = d.get('theory_vs_measured_tau')
    if not isinstance(tv, dict):
        continue
    for k, v in tv.items():
        if isinstance(v, dict) and 'max_abs_diff' in v:
            print('  %-42s -> %-44s max=%s mean=%s n=%s'
                  % (f.split('/')[-1], k, v.get('max_abs_diff'),
                     v.get('mean_abs_diff'), v.get('n')))

print()
print('=== 2) 0.0624 出现在哪个键 ===')
found = False
for f, d in data.items():
    out = []
    walk(d, '', out)
    for v, p in out:
        if abs(v - 0.0624) < 0.0006:
            print('  %-28s %-52s = %s' % (f.split('/')[-1], p, v))
            found = True
if not found:
    print('  两个文件里都没有 0.0624 —— 该值来自别处（需再定位）')

print()
print('=== 3) 每个文件里所有 abs<0.07 的"误差类"键（供比对）===')
for f, d in data.items():
    out = []
    walk(d, '', out)
    print('  --- %s' % f.split('/')[-1])
    for v, p in out:
        pl = p.lower()
        if abs(v) < 0.07 and any(t in pl for t in ('diff', 'err', 'max', 'deviat')):
            print('      %-56s = %s' % (p, v))

print()
print('=== 4) 全库搜索 0.0624 的出处（限 outputs 顶层 JSON）===')
hits = 0
for f in glob.glob('outputs/*.json'):
    try:
        s = open(f, encoding='utf-8').read()
    except Exception:
        continue
    if '0.0624' in s:
        print('  %s' % f)
        hits += 1
        if hits >= 8:
            break
if not hits:
    print('  outputs 顶层 JSON 中无 0.0624 字面出现（可能是计算值，非存储值）')

"""定位并汇总 ODE 拟合结果(Flickr/COCO), 以及 BLIP 实验实际模型。"""
import json
import glob
import os
import re
import numpy as np

print('=== ODE 拟合结果文件 ===')
cands = []
for pat in ['outputs/theory/**/v1_all_results.json',
            'outputs/theory/**/*all_results*.json',
            'outputs/theory/*/results.json',
            'outputs/theory/**/summary*.json']:
    cands += glob.glob(pat, recursive=True)
for f in sorted(set(cands)):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    rs = d if isinstance(d, list) else d.get('all_results', d.get('results', []))
    if not isinstance(rs, list) or not rs:
        continue
    if not isinstance(rs[0], dict) or 'beta' not in rs[0]:
        continue
    betas = [r['beta'] for r in rs if r.get('beta') is not None]
    r2s = [r['r_squared'] for r in rs if r.get('r_squared') is not None]
    if betas:
        print('  %-58s n=%3d beta=%.4f R2=%.4f (pop sd %.4f / sample %.4f) bitfit=%s' % (
            f.replace('D:\\Realdesktop\\Wan\\Important\\New\\', ''), len(betas),
            np.mean(betas), np.mean(r2s), np.std(r2s), np.std(r2s, ddof=1),
            any('bitfit' in str(r.get('name', '')).lower() or 'bias' in str(r.get('name', '')).lower() for r in rs)))

print()
print('=== 按目录计数(Flickr / COCO 各自 config x seed) ===')
for base in ['outputs/theory/v1_flickr', 'outputs/theory/v1_coco', 'outputs/theory/flickr', 'outputs/theory/coco']:
    if os.path.isdir(base):
        n = len(glob.glob(base + '/**/*result*.json', recursive=True))
        cfgs = sorted(set(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(base + '/**/*result*.json', recursive=True)))
        print('  %-28s files=%d configs=%d %s' % (base, n, len(cfgs), cfgs[:8]))

print()
print('=== BLIP 实验列表与实际模型 ===')
try:
    t = open('experiments/blip2_experiments.py', encoding='utf-8').read()
    m = re.search(r'BLIP2_EXPERIMENTS\s*=\s*\[(.*?)\]', t, re.S)
    print('  BLIP2_EXPERIMENTS 片段:', (m.group(1)[:300].replace('\n', ' ') if m else 'NA'))
    for mm in re.finditer(r'(BLIP1_MODEL|BLIP2_MODEL_350M|BLIP2_MODEL_27B)\s*=\s*"([^"]+)"', t):
        print('  ', mm.group(1), '=', mm.group(2))
    used = re.findall(r'model_name\s*=\s*([A-Za-z0-9_]+)', t)
    print('  脚本里 model_name 变量用法:', sorted(set(used))[:6])
except Exception as e:
    print('  NA', e)
for f in sorted(glob.glob('outputs/blip2/*/results.json'))[:4]:
    d = json.load(open(f, encoding='utf-8'))
    print('  ', os.path.basename(os.path.dirname(f)), '->', json.dumps(d, ensure_ascii=False)[:200])

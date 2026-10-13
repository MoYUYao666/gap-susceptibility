"""Recheck the disputed points raised by the number audit: cross-batch Spearman / rank linearity / COCO β / BLIP model / SigLIP / +0.079 / clustering bootstrap."""
import json
import glob
import numpy as np
from scipy import stats

print('=== 1) Cross-batch Spearman (absolute value vs signed) ===')
bl = {}
for tag, f in [('b0', 'outputs/llava_granularity_bootstrap_v2.json'),
               ('b32', 'outputs/llava_granularity_bootstrap_v2_b32.json'),
               ('b64', 'outputs/llava_granularity_bootstrap_v2_b64.json')]:
    d = json.load(open(f, encoding='utf-8'))
    bl[tag] = d['block_mean_gdot']
keys = sorted(set().union(*[set(v) for v in bl.values()]))
for k in keys:
    print('   ', k, [round(bl[t].get(k, float('nan')), 2) for t in ('b0', 'b32', 'b64')])
import itertools
for a, b in itertools.combinations(['b0', 'b32', 'b64'], 2):
    va = [abs(bl[a][k]) for k in keys if k in bl[a] and k in bl[b]]
    vb = [abs(bl[b][k]) for k in keys if k in bl[a] and k in bl[b]]
    r_abs = stats.spearmanr(va, vb)
    vs_a = [bl[a][k] for k in keys if k in bl[a] and k in bl[b]]
    vs_b = [bl[b][k] for k in keys if k in bl[a] and k in bl[b]]
    r_sgn = stats.spearmanr(vs_a, vs_b)
    print('   %s-%s  |G|: rho=%.3f p=%.4f   signed: rho=%.3f p=%.4f' % (a, b, r_abs.statistic, r_abs.pvalue, r_sgn.statistic, r_sgn.pvalue))

print()
print('=== 2) Rank linearity fit (phase-table mean |dE|, 7 finite ranks) ===')
ranks = np.array([4, 5, 6, 7, 8, 16, 20], dtype=float)
dE = np.array([-105.2, -21.0, 62.3, 191.5, 311.3, 1571.5, 2859.7])
y = np.abs(dE)
for name, x in [('rank', ranks), ('log-rank', np.log(ranks))]:
    sl, ic, r, p, se = stats.linregress(x, y)
    print('   %-9s slope=%.1f R2=%.4f p=%.4g' % (name, sl, r ** 2, p))
sp = stats.spearmanr(ranks, y)
print('   spearman(rank, |dE|) rho=%.4f p=%.4g' % (sp.statistic, sp.pvalue))
old = json.load(open('outputs/llava_rank_linearity.json', encoding='utf-8'))
print('   old llava_rank_linearity.json:', old)

print()
print('=== 3) COCO/Flickr ODE table (tab:generalization) ===')
for f in ['outputs/theory/v1_coco/v1_all_results.json', 'outputs/theory/v1_flickr/v1_all_results.json']:
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        print('   NA', f); continue
    rs = d if isinstance(d, list) else d.get('all_results', d.get('results', []))
    betas = [r.get('beta') for r in rs if isinstance(r, dict) and r.get('beta')]
    r2s = [r.get('r_squared') for r in rs if isinstance(r, dict) and r.get('r_squared')]
    if betas:
        print('   %s n=%d beta mean=%.5f  R2 mean=%.5f sd(pop)=%.5f sd(sample)=%.5f' % (
            f, len(betas), np.mean(betas), np.mean(r2s), np.std(r2s), np.std(r2s, ddof=1)))

print()
print('=== 4) BLIP model name (output dir/script) ===')
for f in glob.glob('outputs/blip2/*/results.json')[:2] + glob.glob('experiments/blip2*.py')[:1]:
    t = open(f, encoding='utf-8', errors='ignore').read()
    import re
    m = re.findall(r'(blip[^"\'\s,]{0,30}|BLIP[^"\'\s,]{0,30}|Salesforce[^"\'\s,]{0,30})', t)
    print('   ', f, '->', sorted(set(m))[:6])

print()
print('=== 5) SigLIP / text-only CG values ===')
for f in ['outputs/mechanism_summary.json', 'outputs/domain_matrix.json']:
    try:
        t = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    import re
    for m in re.finditer(r'.{60}siglip.{0,220}', t, re.I):
        print('   ', f, '|', m.group(0).replace('\n', ' ')[:260]); break

"""Recompute the two rows of tab:generalization (Flickr/COCO, unified protocol: all 81 runs)."""
import json
import numpy as np

for label, f in [('Flickr30k', 'outputs/theory/v1_trajectory/v1_all_results.json'),
                 ('COCO', 'outputs/theory/v1_coco/v1_all_results.json')]:
    d = json.load(open(f, encoding='utf-8'))
    rs = d if isinstance(d, list) else d.get('all_results', d.get('results', []))
    print('===', label, 'n =', len(rs))
    print('   sample names:', [r.get('name') for r in rs[:4]])
    alphas = [r['alpha'] for r in rs if r.get('alpha') is not None]
    betas = [r['beta'] for r in rs if r.get('beta') is not None]
    r2s = [r['r_squared'] for r in rs if r.get('r_squared') is not None]
    print('   alpha mean = %.4f (n=%d)' % (np.mean(alphas), len(alphas)))
    print('   beta  mean = %.4f (n=%d)   sd=%.4f' % (np.mean(betas), len(betas), np.std(betas)))
    print('   R2    mean = %.4f (n=%d)   sd(pop)=%.4f sd(sample)=%.4f' % (
        np.mean(r2s), len(r2s), np.std(r2s), np.std(r2s, ddof=1)))
    # config level (aggregated by name prefix)
    from collections import defaultdict
    byc = defaultdict(list)
    for r in rs:
        nm = str(r.get('name', ''))
        byc[nm.rsplit('_s', 1)[0] if '_s' in nm else nm].append(r)
    cfgs = {k: v for k, v in byc.items()}
    if len(cfgs) > 1:
        cmeans_r2 = [np.mean([x['r_squared'] for x in v]) for v in cfgs.values() if v]
        cmeans_b = [np.mean([x['beta'] for x in v]) for v in cfgs.values() if v]
        print('   config-level: n_cfg=%d  R2 mean=%.4f sd=%.4f  beta mean=%.4f' % (
            len(cfgs), np.mean(cmeans_r2), np.std(cmeans_r2), np.mean(cmeans_b)))

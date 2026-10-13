"""Recompute DG-R@1 correlation with clustered bootstrap (config as unit), check paper r=-0.819 / 94 experiments / 79 clusters."""
import json
import numpy as np

d = json.load(open('outputs/master_results.json', encoding='utf-8'))
exp = d['experiments']
rows = []
for key, v in exp.items():
    dg = v.get('dg_init')
    r1 = v.get('R1')
    if dg is None or r1 is None:
        continue
    rows.append({'key': key, 'cluster': key.rsplit('/', 1)[0] if '/' in key else key,
                 'dg': float(dg), 'r1': float(r1)})
print('records with dg_init & R1:', len(rows))
clusters = sorted(set(r['cluster'] for r in rows))
print('clusters:', len(clusters))
for c in clusters:
    n = sum(1 for r in rows if r['cluster'] == c)
    print('   %-40s %d' % (c, n))

dg = np.array([r['dg'] for r in rows])
r1 = np.array([r['r1'] for r in rows])
print('naive pearson (all n=%d): %.4f' % (len(rows), np.corrcoef(dg, r1)[0, 1]))


def pearson(a, b):
    if np.std(a) == 0 or np.std(b) == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


# clustered bootstrap
rng = np.random.RandomState(0)
by_c = {c: [i for i, r in enumerate(rows) if r['cluster'] == c] for c in clusters}
vals = []
for _ in range(10000):
    pick = rng.randint(0, len(clusters), size=len(clusters))
    idx = [i for p in pick for i in by_c[clusters[p]]]
    vals.append(pearson(dg[idx], r1[idx]))
vals = np.array([v for v in vals if not np.isnan(v)])
print('clustered bootstrap: r mean %.4f  95%% CI [%.3f, %.3f]  frac>=0 = %.4f  (n_resamples=%d)' % (
    vals.mean(), np.percentile(vals, 2.5), np.percentile(vals, 97.5), float((vals >= 0).mean()), len(vals)))

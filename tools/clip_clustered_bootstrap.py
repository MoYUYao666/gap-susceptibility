"""DG-R@1 聚配置 bootstrap(可复现版): 记录输入与结果 → outputs/clustered_bootstrap_dg_r1.json"""
import json
import numpy as np

d = json.load(open('outputs/master_results.json', encoding='utf-8'))
exp = d['experiments']
rows = []
for key, v in exp.items():
    if v.get('dg_init') is None or v.get('R1') is None:
        continue
    rows.append({'key': key, 'cluster': key.rsplit('/', 1)[0] if '/' in key else key,
                 'dg': float(v['dg_init']), 'r1': float(v['R1'])})
dg = np.array([r['dg'] for r in rows])
r1 = np.array([r['r1'] for r in rows])
clusters = sorted(set(r['cluster'] for r in rows))
rng = np.random.RandomState(0)
by_c = {c: [i for i, r in enumerate(rows) if r['cluster'] == c] for c in clusters}
vals = []
for _ in range(10000):
    pick = rng.randint(0, len(clusters), size=len(clusters))
    idx = [i for p in pick for i in by_c[clusters[p]]]
    a, b = dg[idx], r1[idx]
    if np.std(a) > 0 and np.std(b) > 0:
        vals.append(float(np.corrcoef(a, b)[0, 1]))
vals = np.array(vals)
out = {
    'inputs': 'outputs/master_results.json :: experiments[*].dg_init vs .R1 (all records with both fields)',
    'n_experiments': len(rows),
    'n_clusters': len(clusters),
    'cluster_unit': 'top-level experiment directory (blip2, coco, flickr30k, flickr30k_seeds/<cfg>, ...)',
    'naive_pearson': round(float(np.corrcoef(dg, r1)[0, 1]), 4),
    'clustered_bootstrap': {'n_resamples': 10000, 'seed': 0,
                            'r_mean': round(float(vals.mean()), 4),
                            'ci95': [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)],
                            'frac_resamples_ge_0': round(float((vals >= 0).mean()), 5)},
    'note': 'replaces the earlier reported -0.819 / 94 experiments / 79 clusters figure, which had no local source script; this version is fully reproducible from master_results.json',
}
json.dump(out, open('outputs/clustered_bootstrap_dg_r1.json', 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))

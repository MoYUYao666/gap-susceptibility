import json, numpy as np
from sklearn.utils import resample
from scipy import stats

with open('master_results.json') as f:
    data = json.load(f)
exps = data['experiments']

# Collect experiments with valid DG and R1
records = []
for path, e in exps.items():
    if e.get('dg_final') is not None and e.get('R1') is not None:
        # Derive config_id: strip seed-specific parts
        # Seeds: path like 'flickr30k_seeds/rq1_rank4/seed42'
        # Non-seeds: path like 'phase1/rq1_rank4'
        norm = path.replace('\\', '/')
        parts = norm.split('/')
        if 'seeds' in parts:
            # Seed experiment: group by config name
            for i, p in enumerate(parts):
                if p == 'seeds' and i+1 < len(parts):
                    config = parts[i+1]  # e.g. 'rq1_rank4'
                    break
            else:
                config = norm
        elif 'flickr30k' in norm or 'coco' in norm:
            # Main experiments: group by base config
            config = parts[-1] if len(parts) > 1 else norm
        else:
            config = norm
        records.append({
            'dg': e['dg_final'],
            'r1': e['R1'],
            'config': config,
            'name': e.get('experiment', path)
        })

print(f'Total experiments with DG+R1: {len(records)}')
n_clusters = len(set(r['config'] for r in records))
print(f'Unique configs (clusters): {n_clusters}')

# Show cluster sizes
from collections import Counter
cfg_counts = Counter(r['config'] for r in records)
print(f'Cluster sizes: min={min(cfg_counts.values())}, max={max(cfg_counts.values())}, mean={np.mean(list(cfg_counts.values())):.1f}')

# Standard Pearson (naive)
r_all = np.array([r['dg'] for r in records])
r1_all = np.array([r['r1'] for r in records])
pearson_r, pearson_p = stats.pearsonr(r_all, r1_all)
print(f'\n=== Naive Pearson (n={len(records)}) ===')
print(f'r = {pearson_r:.4f}, p = {pearson_p:.2e}')

# Clustered bootstrap
configs = list(cfg_counts.keys())
cfg_to_records = {}
for r in records:
    cfg_to_records.setdefault(r['config'], []).append(r)

n_boot = 10000
boot_corrs = np.zeros(n_boot)
rng = np.random.RandomState(42)

for i in range(n_boot):
    sampled_configs = rng.choice(configs, size=len(configs), replace=True)
    boot_dg, boot_r1 = [], []
    for cfg in sampled_configs:
        for rec in cfg_to_records[cfg]:
            boot_dg.append(rec['dg'])
            boot_r1.append(rec['r1'])
    boot_corrs[i], _ = stats.pearsonr(boot_dg, boot_r1)

ci_lower, ci_upper = np.percentile(boot_corrs, [2.5, 97.5])

# P-value: H0: r >= 0 (one-sided, since our hypothesis is r < 0)
p_one = np.mean(boot_corrs >= 0)
# Two-sided H0: r = 0
p_two = np.mean(np.abs(boot_corrs - np.mean(boot_corrs)) >= np.abs(pearson_r - np.mean(boot_corrs)))

print(f'\n=== Clustered Bootstrap ({n_boot} resamples) ===')
print(f'Bootstrap mean r = {np.mean(boot_corrs):.4f}')
print(f'Bootstrap std r  = {np.std(boot_corrs):.4f}')
print(f'95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]')

# Simpler p-value: fraction where boot r >= 0
p_cluster = np.mean(boot_corrs >= 0)
print(f'\nCluster-robust p (H0 r>=0, one-sided): {p_cluster:.6f}')

print(f'\n=== Summary ===')
print(f'Naive r:           {pearson_r:.4f} [p={pearson_p:.2e}]')
print(f'Cluster-mean r:    {np.mean(boot_corrs):.4f}')
print(f'Cluster 95% CI:    [{ci_lower:.4f}, {ci_upper:.4f}]')
print(f'Attenuation:       {abs(pearson_r) - abs(np.mean(boot_corrs)):.4f}')
sig = 'YES' if ci_upper < 0 else 'NO'
print(f'Significant?       {sig}')

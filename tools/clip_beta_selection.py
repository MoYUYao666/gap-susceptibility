"""(full version) β selection criterion: over the 4-block |Γ| estimated without bias for LLaVA r8, sweep the β grid of the exponential allocation policy,
giving a quantitative criterion: β* = 1/σ(Γ) (softmin temperature ≈ Γ spread) + objective efficiency/entropy/separation diagnostics.
Output: outputs/clip_beta_selection.json
"""
import json
import numpy as np

SRC = 'outputs/allocation_policy_sim.json'
OUT = 'outputs/clip_beta_selection.json'

d = json.load(open(SRC, encoding='utf-8'))
blocks = d['blocks']
g = np.array([d['gamma_abs'][b] for b in blocks], dtype=float)
C = d['budget']
assert C == 64


def softmin_alloc(beta):
    w = np.exp(-beta * g)
    w = w / w.sum() * C
    # largest-remainder rounding, guaranteeing the sum is C
    fl = np.floor(w)
    rem = C - fl.sum()
    idx = np.argsort(-(w - fl))
    out = fl.copy().astype(int)
    for i in idx[:int(rem)]:
        out[i] += 1
    return out


def obj(alloc):
    return float((g * alloc).sum())


greedy = np.zeros(4, dtype=int)
greedy[int(np.argmin(g))] = C
uniform = np.full(4, C // 4, dtype=int)

betas = [1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]
rows = []
for b in betas:
    a = softmin_alloc(b)
    o = obj(a)
    rows.append({'beta': b, 'alloc': {blocks[i]: int(a[i]) for i in range(4)},
                 'obj': round(o, 1),
                 'obj_vs_uniform_pct': round((d['policies']['uniform']['obj'] / o - 1) * 100, 1),
                 'eff_vs_greedy_pct': round((o / d['policies']['greedy(lowest|Gamma|)']['obj'] - 1) * 100, 1),
                 'beta_sigma': round(float(b * g.std()), 3)})

# separation and criterion
sigma = float(g.std())
mu = float(g.mean())
rng_sorted = np.sort(g)
adj_gap = float(np.min(np.diff(rng_sorted)))
sep = {'max_min_ratio': round(float(g.max() / g.min()), 2),
       'mean_abs': round(mu, 1), 'std': round(sigma, 1),
       'min_adjacent_ratio_gap': round(adj_gap, 1),
       'adjacent_ratio_gaps': [round(float(x), 1) for x in np.diff(rng_sorted)]}
criterion = {
    'rule': 'beta* = 1 / sigma(|Gamma|)  (softmin temperature equals the Gamma spread)',
    'beta_star': round(1.0 / sigma, 6),
    'beta_low': round(1.0 / (2 * sigma), 6),
    'beta_high': round(2.0 / sigma, 6),
    'note': ('criterion: choose beta in [1/(2 sigma), 2/sigma]; beta* = 1/sigma gives '
             'temperature ~ one std of the block susceptibility; beta>>2/sigma degenerates '
             'to greedy (single block), beta<<1/(2 sigma) degenerates to uniform')}
a_star = softmin_alloc(criterion['beta_star'])
rows.append({'beta': criterion['beta_star'], 'alloc': {blocks[i]: int(a_star[i]) for i in range(4)},
             'obj': round(obj(a_star), 1),
             'obj_vs_uniform_pct': round((d['policies']['uniform']['obj'] / obj(a_star) - 1) * 100, 1),
             'eff_vs_greedy_pct': round((obj(a_star) / d['policies']['greedy(lowest|Gamma|)']['obj'] - 1) * 100, 1),
             'beta_sigma': round(float(criterion['beta_star'] * sigma), 3), 'is_star': True})

out = {'source': SRC, 'blocks': blocks, 'gamma_abs': {b: d['gamma_abs'][b] for b in blocks},
       'budget': C,
       'separation': sep, 'criterion': criterion,
       'grid': rows, 'reference': {'uniform_obj': d['policies']['uniform']['obj'],
                                   'greedy_obj': d['policies']['greedy(lowest|Gamma|)']['obj'],
                                   'uniform_alloc': {blocks[i]: int(uniform[i]) for i in range(4)},
                                   'greedy_alloc': {blocks[i]: int(greedy[i]) for i in range(4)}}}
json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1)
print('DONE ->', OUT, flush=True)
print('sep:', sep, flush=True)
print('criterion:', criterion, flush=True)
for r in sorted(rows, key=lambda x: x['beta']):
    star = ' *' if r.get('is_star') else '  '
    print(f"b={r['beta']:.6f}{star} alloc={r['alloc']} obj={r['obj']:.0f} vs_uniform=+{r['obj_vs_uniform_pct']:.1f}% vs_greedy=+{r['eff_vs_greedy_pct']:.1f}% beta_sigma={r['beta_sigma']:.2f}", flush=True)

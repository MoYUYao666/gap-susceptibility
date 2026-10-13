"""(A4 + statistics audit) Reproducible recomputation of the statistical tests in the phase-transition chapter, two data families:

Family A ("paper family", for reproduction): the 7 tests reported in §6 of the paper, data from the three batches of tab:phase
  - E2_results.json :: E2     (r4, r16 with 3 seeds each; E0=3930.5)
  - E2_results.json :: extra  (r5,r6,r7,r8 with 3 seeds each, E0=3927.0)
  - E2_results.json :: sweep  (r20, r≥24; dense sweep in the old environment, the paper uses it only for r20 and collapse)
  Test definitions (all hard-coded):
   1 pooled_45_vs_67 : {E2 r4} ∪ {extra r5} vs {extra r6} ∪ {extra r7}, Welch t (n=6 each)
   2 welch_56_ds2    : second dataset (vqa_phase_results.json) r5 vs r6, Welch t (n=3+3)
   3 ds2_r6_vs0      : second dataset r6 one-sample two-sided t (n=3)
   4 ds2_r5_vs0      : second dataset r5 one-sample two-sided t (n=3)
   5 llava_r5_vs0    : LLaVA (extra) r5 one-sample two-sided t (n=3)
   6 llava_r6_vs0    : LLaVA (extra) r6 one-sample two-sided t (n=3)
   7 config_ordering : config-level ΔE(r6)>ΔE(r5) (sample sizes n∈{16,64,128,256} + tab:phase means + second-dataset means),
                       exact two-sided binomial

Family B ("independent replication family", new in Tier A4): independent seed batches of the reference protocol in the current environment
  paper3/scripts/outputs/experiments/verify_r{N}_s{M}.json (default protocol, no labels; includes the new A4 seeds)
  → mean±CI, one-sample t and Welch for r=5 / r=6, plus the ordering count for {5} vs {6}

Output: outputs/phase_stats_recompute.json
"""
import glob
import json
import math
import os
import re

import numpy as np
from scipy import stats

EXP = 'paper3/scripts/outputs/experiments'
OUT = 'outputs/phase_stats_recompute.json'
PAPER_P = {'pooled_45_vs_67': 0.0014, 'welch_56_ds2': 0.011, 'ds2_r6_vs0': 0.013,
           'ds2_r5_vs0': 0.92, 'config_ordering': 0.031, 'llava_r6_vs0': 0.17,
           'llava_r5_vs0': 0.37}


def binom_two_sided(k, n, p=0.5):
    from math import comb
    pmf = lambda i: comb(n, i) * p ** i * (1 - p) ** (n - i)
    obs, tol = pmf(k), 1e-12
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs + tol))


def de(entry):
    E = entry.get('E') or []
    if len(E) < 2:
        return None
    v = E[-1]
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v - E[0])


def load_paper_batches():
    d = json.load(open(os.path.join(EXP, 'E2_results.json'), encoding='utf-8'))
    out = {}
    for batch in ('E2', 'extra', 'sweep'):
        for e in d.get(batch, []):
            v = de(e)
            if v is None:
                continue
            out.setdefault(e['rank'], []).append({'batch': batch, 'seed': e['seed'], 'dE': v})
    return out


def load_replication():
    """Default-protocol runs of the reference protocol in the current environment (including the new A4 seeds)."""
    out = {}
    for p in glob.glob(os.path.join(EXP, 'verify_r*_s*.json')):
        if not re.match(r'^verify_r\d+_s\d+\.json$', os.path.basename(p)):
            continue
        d = json.load(open(p, encoding='utf-8'))
        if d.get('epochs') != 3:
            continue
        v = d.get('delta_E')
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        out.setdefault(int(d['rank']), {})[int(d['seed'])] = float(v)
    return out


def main():
    pb = load_paper_batches()
    rep = load_replication()
    ds2 = json.load(open(os.path.join(EXP, 'vqa_phase_results.json'), encoding='utf-8'))
    ss = json.load(open(os.path.join(EXP, 'sample_size_results.json'), encoding='utf-8'))['runs']
    ss_de = {}
    for r in ss:
        ss_de.setdefault(r['rank'], []).append(r['E'][-1] - r['E'][0])

    tests = []

    def add(name, p, desc, n=None, family='paper', paper=None):
        tests.append({'name': name, 'p': round(float(p), 5), 'desc': desc, 'n': n,
                      'family': family, 'paper_p': paper})

    def pick(rank, batches):
        """Return the ΔE list for the batch selection of tab:phase (r4/r16←E2, r5-r8←extra, r20←sweep)."""
        return [x['dE'] for x in pb.get(rank, []) if x['batch'] in batches]

    # --- family A ---
    lo = pick(4, ('E2',)) + pick(5, ('extra',))
    hi = pick(6, ('extra',)) + pick(7, ('extra',))
    if lo and hi:
        t, p = stats.ttest_ind(lo, hi, equal_var=False)
        add('pooled_45_vs_67', p, f'phase-table batches: r{{4,5}} (n={len(lo)}) vs r{{6,7}} (n={len(hi)}), '
                                  f'Welch t={t:.2f}', len(lo) + len(hi), paper=PAPER_P['pooled_45_vs_67'])
    v5 = ds2.get('r5', {}).get('dE', [])
    v6 = ds2.get('r6', {}).get('dE', [])
    if v5 and v6:
        t, p = stats.ttest_ind(v5, v6, equal_var=False)
        add('welch_56_ds2', p, f'second dataset Welch t r=5 vs r=6, t={t:.2f}', len(v5) + len(v6),
            paper=PAPER_P['welch_56_ds2'])
    if v6:
        t, p = stats.ttest_1samp(v6, 0.0)
        add('ds2_r6_vs0', p, f'second dataset r=6 one-sample t vs 0, t={t:.2f}, mean={np.mean(v6):.1f}',
            len(v6), paper=PAPER_P['ds2_r6_vs0'])
    if v5:
        t, p = stats.ttest_1samp(v5, 0.0)
        add('ds2_r5_vs0', p, f'second dataset r=5 one-sample t vs 0, t={t:.2f}, mean={np.mean(v5):.1f}',
            len(v5), paper=PAPER_P['ds2_r5_vs0'])
    for r, nm in ((5, 'llava_r5_vs0'), (6, 'llava_r6_vs0')):
        vals = pick(r, ('extra',))
        if vals:
            t, p = stats.ttest_1samp(vals, 0.0)
            add(nm, p, f'phase-table LLaVA r={r} one-sample t vs 0, t={t:.2f}, mean={np.mean(vals):.1f}',
                len(vals), paper=PAPER_P[nm])
    configs = {}
    for n in (16, 64, 128, 256):
        d = {r['rank']: r['E'][-1] - r['E'][0] for r in ss if r['samples'] == n}
        if 5 in d and 6 in d:
            configs[f'samples_{n}'] = {'r5': d[5], 'r6': d[6], 'ordered': d[6] > d[5]}
    if 5 in pb and 6 in pb:
        e5, e6 = pick(5, ('extra',)), pick(6, ('extra',))
        m5, m6 = float(np.mean(e5)), float(np.mean(e6))
        configs['phase_table'] = {'r5': round(m5, 2), 'r6': round(m6, 2), 'ordered': m6 > m5}
    if v5 and v6:
        configs['second_dataset'] = {'r5': round(float(np.mean(v5)), 2), 'r6': round(float(np.mean(v6)), 2),
                                     'ordered': float(np.mean(v6)) > float(np.mean(v5))}
    k = sum(1 for c in configs.values() if c['ordered'])
    add('config_ordering', binom_two_sided(k, len(configs)),
        f'config-level ΔE(r6)>ΔE(r5) in {k}/{len(configs)} configs, exact two-sided binomial',
        len(configs), paper=PAPER_P['config_ordering'])

    # --- family B: independent replication family ---
    rep_stats = {}
    for r in (5, 6):
        vals = np.array(list(rep.get(r, {}).values()), dtype=float)
        if len(vals) >= 2:
            ci = stats.t.interval(0.95, len(vals) - 1, loc=vals.mean(), scale=stats.sem(vals))
            t, p = stats.ttest_1samp(vals, 0.0)
            rep_stats[f'r{r}'] = {'n': int(len(vals)), 'seeds': sorted(rep[r]),
                                  'mean': round(float(vals.mean()), 2), 'std': round(float(vals.std(ddof=1)), 2),
                                  'ci95': [round(float(ci[0]), 1), round(float(ci[1]), 1)],
                                  't': round(float(t), 3), 'p_vs0': round(float(p), 5),
                                  'n_positive': int((vals > 0).sum())}
    if 'r5' in rep_stats and 'r6' in rep_stats:
        a, b = list(rep[5].values()), list(rep[6].values())
        t, p = stats.ttest_ind(a, b, equal_var=False)
        rep_stats['welch_56'] = {'t': round(float(t), 3), 'p': round(float(p), 5), 'n': [len(a), len(b)]}
        rep_stats['ordering_r6_gt_r5'] = {
            'mean_r5': round(float(np.mean(a)), 2), 'mean_r6': round(float(np.mean(b)), 2),
            'holds': bool(np.mean(b) > np.mean(a)),
            'per_seed_pairs': [{'seed': s, 'r5': rep[5][s], 'r6': rep[6][s],
                                'holds': rep[6][s] > rep[5][s]} for s in sorted(set(rep[5]) & set(rep[6]))]}
        n_pairs = len(rep_stats['ordering_r6_gt_r5']['per_seed_pairs'])
        n_hold = sum(1 for d in rep_stats['ordering_r6_gt_r5']['per_seed_pairs'] if d['holds'])
        rep_stats['ordering_r6_gt_r5']['n_hold'] = n_hold
        rep_stats['ordering_r6_gt_r5']['binom_two_sided_p'] = round(binom_two_sided(n_hold, n_pairs), 5)
        # BH-FDR for the independent replication family itself (4 items: r5 vs 0 / r6 vs 0 / Welch 5-6 / per-seed ordering)
        rep_tests = [('r5_vs0', rep_stats['r5']['p_vs0']), ('r6_vs0', rep_stats['r6']['p_vs0']),
                     ('welch_56', rep_stats['welch_56']['p']),
                     ('per_seed_ordering', rep_stats['ordering_r6_gt_r5']['binom_two_sided_p'])]
        ps_r = np.array([p for _, p in rep_tests])
        order_r = np.argsort(ps_r)
        raw_r = np.array([ps_r[i] * len(ps_r) / (rank + 1) for rank, i in enumerate(order_r)])
        q_r = np.minimum.accumulate(raw_r[::-1])[::-1]
        rep_stats['bh_fdr'] = [{'name': rep_tests[i][0], 'p': round(float(ps_r[i]), 5),
                                'rank': rank, 'bh_q': round(float(q_r[rank - 1]), 4),
                                'survives_005': bool(q_r[rank - 1] <= 0.05),
                                'survives_010': bool(q_r[rank - 1] <= 0.10)}
                               for rank, i in enumerate(order_r, 1)]

    # --- BH-FDR (family A, aligned with the paper's 7-test family) ---
    def bh_over(fam):
        sub = [t for t in tests if t['family'] == fam]
        ps = np.array([t['p'] for t in sub])
        m = len(ps)
        order = np.argsort(ps)
        raw = np.array([ps[i] * m / (rank + 1) for rank, i in enumerate(order)])
        q = np.minimum.accumulate(raw[::-1])[::-1]
        out = []
        for rank, i in enumerate(order, 1):
            pp = float(ps[i])
            paper = sub[i]['paper_p']
            ok = None if paper is None else bool(abs(pp - paper) <= max(0.01, 0.05 * paper))
            out.append({'name': sub[i]['name'], 'p': round(pp, 5), 'rank': rank,
                        'bh_q': round(float(q[rank - 1]), 4),
                        'survives_005': bool(q[rank - 1] <= 0.05), 'survives_010': bool(q[rank - 1] <= 0.10),
                        'paper_p': paper, 'reproduces_paper': ok, 'desc': sub[i]['desc'], 'n': sub[i]['n']})
        return out

    bh = bh_over('paper')
    summary = {
        'paper_batches': {str(r): sorted(x['batch'] + ':s%d' % x['seed'] for x in v) for r, v in sorted(pb.items())},
        'configs': configs,
        'n_tests': len(tests),
        'reproduced_paper_values': [b['name'] for b in bh if b['reproduces_paper']],
        'not_reproduced': [b['name'] for b in bh if b['reproduces_paper'] is False],
        'survive_005': [b['name'] for b in bh if b['survives_005']],
        'survive_010': [b['name'] for b in bh if b['survives_010']],
        'replication_family': rep_stats,
    }
    json.dump({'tests': tests, 'bh_fdr': bh, 'summary': summary},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('%-18s %-10s %-10s %-8s %-6s %s' % ('test', 'p', 'paper_p', 'bh_q', 's005', 'repro'), flush=True)
    for b in bh:
        print('%-18s %-10s %-10s %-8s %-6s %s' % (b['name'], b['p'], b['paper_p'], b['bh_q'],
                                                  b['survives_005'], b['reproduces_paper']), flush=True)
    print('configs:', json.dumps(configs), flush=True)
    print('replication:', json.dumps(rep_stats, indent=1), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()

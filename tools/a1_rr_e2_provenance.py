"""A1 revision -- provenance probe for the published tau/accuracy Spearman (0.9262).

outputs/a1_baseline_metrics.json (the source of the manuscript's headline "Spearman(tau, top-1)
= 0.926, p = 1.19e-11") stores only the four summary correlations and not the per-condition
vectors, so it cannot be reproduced directly. This probe asks which (k, condition-grid) combination
of my E2 recomputation reproduces those four stored numbers exactly:

    tau       r = 0.9262  p = 1.1861084080501641e-11
    CG        r = -0.0821 p = 0.6900201423221363
    cka       r = 0.7552  p = 8.218838697506625e-06
    mean_cos  r = 0.8715  p = 6.8676414868445615e-09

Inputs : outputs/a1_rr_e2_topk.json (E2 recomputation), outputs/a1_baseline_metrics.json (published)
Output : outputs/a1_rr_e2_provenance.json
Run    : D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_rr_e2_provenance.py
"""
import json

import numpy as np
from scipy import stats

E2 = 'outputs/a1_rr_e2_topk.json'
PUB = 'outputs/a1_baseline_metrics.json'
OUT = 'outputs/a1_rr_e2_provenance.json'


def main():
    e2 = json.load(open(E2, encoding='utf-8'))
    pub = json.load(open(PUB, encoding='utf-8'))['metric_correlations']
    t1_all = {c['name']: c for c in e2['conditions_shared']}
    grid26 = set(e2['meta']['grid26_names'])

    def top1(conv, name):
        return t1_all[name]['top1_legacy1001' if conv == 'legacy1001' else 'top1_clean1000']

    out = {'meta': {'script': 'tools/a1_rr_e2_provenance.py', 'inputs': [E2, PUB],
                    'published': pub,
                    'note': 'published a1_baseline_metrics.json stores no per-condition values; '
                            'this probe compares full-precision recomputations against it.'},
           'tau_matches': [], 'metric_matches': {}}

    for conv in ('legacy1001', 'clean1000'):
        L = e2['conventions'][conv]
        for variant, names in (('26cond', [n for n in t1_all if n in grid26]),
                               ('27cond_incl_T-2', list(t1_all))):
            for k in e2['meta']['ks']:
                taus = L['per_k'][str(k)]['tau']
                ns = [n for n in names if taus.get(n) is not None]
                if len(ns) < 3:
                    continue
                v = [taus[n] for n in ns]
                tv = [top1(conv, n) for n in ns]
                r, p = stats.spearmanr(v, tv)
                row = {'convention': conv, 'grid': variant, 'k': k, 'n': len(ns),
                       'r': float(r), 'p': float(p),
                       'p_matches_published_exactly': bool(p == pub['tau']['p'])}
                out['tau_matches'].append(row)
            for metric in ('CG', 'cka', 'mean_cos'):
                v = [t1_all[n][metric] for n in names]
                tv = [top1(conv, n) for n in names]
                r, p = stats.spearmanr(v, tv)
                out['metric_matches'].setdefault(metric, []).append(
                    {'convention': conv, 'grid': variant, 'n': len(names), 'r': float(r), 'p': float(p),
                     'published_r': pub[metric]['spearman_r'], 'published_p': pub[metric]['p'],
                     'p_matches_published_exactly': bool(p == pub[metric]['p'])})

    hits = [r for r in out['tau_matches'] if r['p_matches_published_exactly']]
    out['verdict'] = {
        'exact_tau_matches': hits,
        'n_exact_tau_matches': len(hits),
        'conclusion': ('the only recomputation that reproduces the stored tau correlation to '
                       'machine precision is the k=10 tau on the archived 26-condition grid; the '
                       'k=5 value of the same grid is 0.9125. tools/clip_a1_baseline_metrics.py '
                       'as it stands computes k=5, so the stored JSON was produced by a variant '
                       'that used top-10 class sets (the variable there is still named topk5).'
                       if len(hits) == 1 and hits[0]['k'] == 10 else
                       'multiple or no exact matches found -- see exact_tau_matches'),
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print('published tau Spearman: r=%.6f p=%.16g' % (pub['tau']['spearman_r'], pub['tau']['p']))
    print('\nexact matches of the published tau p-value:')
    for h in hits:
        print('  %s' % h)
    print('\nall k on the 26-condition grid (legacy1001):')
    for r in out['tau_matches']:
        if r['convention'] == 'legacy1001' and r['grid'] == '26cond':
            print('  k=%-4s r=%.12f p=%.16g exact=%s'
                  % (r['k'], r['r'], r['p'], r['p_matches_published_exactly']))
    print('\nk-independent metrics vs published:')
    for m, rows in out['metric_matches'].items():
        for r in rows:
            print('  %-9s %-8s %-15s r=%+.6f (published %+.6f)  exact_p=%s'
                  % (m, r['convention'], r['grid'], r['r'], r['published_r'],
                     r['p_matches_published_exactly']))
    print('\nsaved', OUT)


if __name__ == '__main__':
    main()

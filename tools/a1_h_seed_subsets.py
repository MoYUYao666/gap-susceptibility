"""A1 post-merge fix, item P6 -- give the two seed-sweep statistics a stored provenance.

The merged manuscript `paper_a1/main.tex` quoted two numbers that existed in no file under
`outputs/` (only in `docs/A1_HARDENING.md` prose):

  (i)  dropping the DTD family (n = 6) *reverses* the tau-vs-gap comparison: tau falls to
       +0.486 (p = 0.33) against CG +0.657 (p = 0.16);
  (ii) across the 27 one-seed-per-dataset subsets tau's rank correlation is +1.00 in 21 of
       them and +0.50 in the other 6.

Both are pure arithmetic over the nine controlled checkpoints of the seed sweep (three seeds
42/43/44 x three datasets COCO/Food-101/DTD) already recorded in
`outputs/a1_h_seed_summary.json::runs`. This script enumerates the member sets explicitly and
recomputes the correlations, so that every number in those two sentences has a recorded source.

Definitions used (stated because the manuscript does not state them):

  * tau5          = Kendall order preservation on the frozen top-5 class sets, 5 000-image
                    sample (`runs[*].tau5`).
  * top-1         = full 50 000-image validation accuracy (`runs[*].top1_50k`); this is the
                    accuracy column the manuscript's seed paragraph uses ("50{,}000-image
                    top-1 standard deviations of 0.58, 0.48 and 0.65 points").
  * correlation   = **Spearman** rank correlation (the manuscript's word is "rank
                    correlation", and the contrast it draws is the rank-based one used
                    everywhere else in the seed paragraph: +0.85 / -0.27 over nine runs).
                    Kendall and Pearson are reported alongside for completeness.
  * drop-DTD set  = the six runs whose dataset is COCO or Food-101 (all three seeds each).
  * subset family = every way of picking exactly one seed per dataset: 3 x 3 x 3 = 27 subsets
                    of three runs, each correlated across its three datasets.

Output: outputs/a1_h_seed_subsets.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_seed_subsets.py
"""
import os
import json
import hashlib
import itertools
from datetime import datetime, timezone

import numpy as np
from scipy import stats

SRC = 'outputs/a1_h_seed_summary.json'
OUT = 'outputs/a1_h_seed_subsets.json'

DATASETS = ['coco', 'food101', 'dtd']
SEEDS = [42, 43, 44]

# The two claims as printed in the merged manuscript (P6), for a stored agree/disagree verdict.
CLAIM_DROP_DTD = {'tau_spearman_r': 0.486, 'tau_p': 0.33, 'cg_spearman_r': 0.657, 'cg_p': 0.16}
CLAIM_SUBSETS = {'n_subsets': 27, 'rho_plus_1': 21, 'rho_plus_half': 6}


def file_sha1(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def correlate(x, y):
    """Spearman (primary) plus Kendall and Pearson, all with p-values."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    sp = stats.spearmanr(x, y)
    kt = stats.kendalltau(x, y)
    pe = stats.pearsonr(x, y)
    return {
        'n': int(x.size),
        'spearman_r': round(float(sp.statistic), 10),
        'spearman_p': float(sp.pvalue),
        'kendall_r': round(float(kt.statistic), 10),
        'kendall_p': float(kt.pvalue),
        'pearson_r': round(float(pe.statistic), 10),
        'pearson_p': float(pe.pvalue),
    }


def main():
    src = load(SRC)
    runs = src['runs']

    by_dataset = {}
    for r in runs:
        by_dataset.setdefault(r['dataset'], {})[r['seed']] = r

    missing = [(d, s) for d in DATASETS for s in SEEDS if s not in by_dataset.get(d, {})]
    if missing:
        raise SystemExit('missing runs in %s: %s' % (SRC, missing))

    run_set = []
    for d in DATASETS:
        for s in SEEDS:
            r = by_dataset[d][s]
            run_set.append({'dataset': d, 'seed': s, 'tau5': r['tau5'],
                            'top1_50k': r['top1_50k'], 'top1_5k': r['top1_5k'],
                            'CG': r['CG'], 'n_steps': r.get('n_steps')})

    # ---------------------------------------------------------------- (i) drop-DTD, n = 6
    dropped = 'dtd'
    sub = [r for r in run_set if r['dataset'] != dropped]
    drop_dtd = {
        'label': 'coco+food101, seeds 42/43/44 (DTD dropped)',
        'dropped_family': dropped,
        'n': len(sub),
        'members': ['%s_seed%d' % (r['dataset'], r['seed']) for r in sub],
        'tau5': [r['tau5'] for r in sub],
        'top1_50k': [r['top1_50k'] for r in sub],
        'CG': [r['CG'] for r in sub],
        'tau5_vs_top1_50k': correlate([r['tau5'] for r in sub], [r['top1_50k'] for r in sub]),
        'CG_vs_top1_50k': correlate([r['CG'] for r in sub], [r['top1_50k'] for r in sub]),
    }
    drop_dtd['manuscript_claim'] = dict(CLAIM_DROP_DTD)
    drop_dtd['agrees_with_manuscript'] = bool(
        abs(drop_dtd['tau5_vs_top1_50k']['spearman_r'] - CLAIM_DROP_DTD['tau_spearman_r']) <= 5e-4
        and abs(drop_dtd['tau5_vs_top1_50k']['spearman_p'] - CLAIM_DROP_DTD['tau_p']) <= 5e-3
        and abs(drop_dtd['CG_vs_top1_50k']['spearman_r'] - CLAIM_DROP_DTD['cg_spearman_r']) <= 5e-4
        and abs(drop_dtd['CG_vs_top1_50k']['spearman_p'] - CLAIM_DROP_DTD['cg_p']) <= 5e-3)
    drop_dtd['rounds_to_manuscript'] = {
        'tau_spearman_r': round(drop_dtd['tau5_vs_top1_50k']['spearman_r'], 3),
        'tau_p': round(drop_dtd['tau5_vs_top1_50k']['spearman_p'], 2),
        'cg_spearman_r': round(drop_dtd['CG_vs_top1_50k']['spearman_r'], 3),
        'cg_p': round(drop_dtd['CG_vs_top1_50k']['spearman_p'], 2),
    }

    # ------------------------------------- (ii) 27 one-seed-per-dataset subsets, n = 3 each
    subsets = []
    distribution = {}
    for combo in itertools.product(SEEDS, repeat=len(DATASETS)):
        sel = dict(zip(DATASETS, combo))
        rows = [by_dataset[d][sel[d]] for d in DATASETS]
        c = correlate([r['tau5'] for r in rows], [r['top1_50k'] for r in rows])
        key = '%.2f' % c['spearman_r']
        distribution[key] = distribution.get(key, 0) + 1
        subsets.append({
            'seeds': sel,
            'members': ['%s_seed%d' % (d, sel[d]) for d in DATASETS],
            'tau5': [r['tau5'] for r in rows],
            'top1_50k': [r['top1_50k'] for r in rows],
            'spearman_r': c['spearman_r'],
            'spearman_p': c['spearman_p'],
        })

    n_plus_1 = distribution.get('1.00', 0)
    n_plus_half = distribution.get('0.50', 0)
    subsets_block = {
        'definition': 'every way of picking exactly one seed per dataset (3^3 = 27 subsets of '
                      'three runs); Spearman(tau5, top1_50k) computed within each subset',
        'n_subsets': len(subsets),
        'distribution_spearman_r': distribution,
        'n_with_rho_plus_1': n_plus_1,
        'n_with_rho_plus_half': n_plus_half,
        'other_rho_values': sorted(k for k in distribution if k not in ('1.00', '0.50')),
        'manuscript_claim': dict(CLAIM_SUBSETS),
        'agrees_with_manuscript': bool(len(subsets) == CLAIM_SUBSETS['n_subsets']
                                       and n_plus_1 == CLAIM_SUBSETS['rho_plus_1']
                                       and n_plus_half == CLAIM_SUBSETS['rho_plus_half']),
        'subsets': subsets,
    }

    out = {
        'meta': {
            'script': os.path.basename(__file__),
            'script_path': 'tools/a1_h_seed_subsets.py',
            'purpose': 'item P6 -- provenance for two seed-sweep statistics quoted in the merged '
                       'manuscript (drop-DTD reversal, and the 27 one-seed-per-dataset subsets)',
            'inputs': {SRC: file_sha1(SRC)},
            'datasets': DATASETS,
            'seeds': SEEDS,
            'correlation_variant': 'spearman (kendall and pearson also recorded)',
            'tau_definition': 'Kendall order preservation on the frozen top-5 class sets, '
                              '5000-image sample (runs[*].tau5)',
            'accuracy_definition': 'top-1 on the full 50000-image validation set (runs[*].top1_50k)',
            'provenance': 'pure arithmetic over runs[*] of the input; no model is re-evaluated',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        },
        'run_set': run_set,
        'drop_dtd_n6': drop_dtd,
        'one_seed_per_dataset_subsets': subsets_block,
        'verdict': {
            'drop_dtd_reproduces': drop_dtd['agrees_with_manuscript'],
            'subset_split_reproduces': subsets_block['agrees_with_manuscript'],
            'manuscript_text_needs_correction': bool(not drop_dtd['agrees_with_manuscript']
                                                     or not subsets_block['agrees_with_manuscript']),
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print('wrote', OUT)
    print('drop-DTD n=%d  tau: rho=%+.4f p=%.4f | CG: rho=%+.4f p=%.4f'
          % (drop_dtd['n'], drop_dtd['tau5_vs_top1_50k']['spearman_r'],
             drop_dtd['tau5_vs_top1_50k']['spearman_p'],
             drop_dtd['CG_vs_top1_50k']['spearman_r'],
             drop_dtd['CG_vs_top1_50k']['spearman_p']))
    print('27 subsets distribution:', distribution)
    print('agrees with manuscript:',
          drop_dtd['agrees_with_manuscript'], subsets_block['agrees_with_manuscript'])


if __name__ == '__main__':
    main()

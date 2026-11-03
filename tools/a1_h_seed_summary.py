"""A1 hardening item 2 (analysis) -- seed spread for the non-Flickr30k checkpoints.

Reads the three seed-42 runs (`outputs/a1_rr_e4_{coco,food101,dtd}.json`, produced by
`tools/a1_rr_e4_train.py`) plus the six new seed-43/44 runs (`outputs/a1_h_seeds_*.json`, produced
by `tools/a1_h_e4_seed.py`, an otherwise verbatim copy of the same trainer) and reports:

  * per dataset, the three seeds' tau@k=5, top-1 (5k and 50k) and CG, with mean +/- sample sd and
    range;
  * the cross-checkpoint Spearman/Pearson of tau vs top-1 and CG vs top-1 over the FULL checkpoint
    set including the seed spread, and over the seed-42-only set for comparison, so it is visible
    whether the "tau correlates with accuracy better than the gap does" contrast survives;
  * whether tau's WITHIN-dataset ranking of the three seeds is stable across datasets and
    consistent with accuracy;
  * where each checkpoint sits relative to the synthetic tau->top-1 curve.

Everything is read from JSONs; nothing is recomputed from the model here, so this script is pure
arithmetic over recorded numbers.
Output: outputs/a1_h_seed_summary.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_seed_summary.py
"""
import os
import sys
import json
import glob
import hashlib
from datetime import datetime, timezone

import numpy as np
from scipy import stats

BASE = {'coco': 'outputs/a1_rr_e4_coco.json',
        'food101': 'outputs/a1_rr_e4_food101.json',
        'dtd': 'outputs/a1_rr_e4_dtd.json',
        'flickr30k_ref': 'outputs/a1_rr_e4_flickr30k_ref.json'}
SEED_JSON = 'outputs/a1_h_seeds_%s_seed%d.json'
SEEDS = [42, 43, 44]
E2 = 'outputs/a1_rr_e2_topk.json'
OUT = 'outputs/a1_h_seed_summary.json'


def file_sha1(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def summarise(vals):
    a = np.asarray([v for v in vals if v is not None], dtype=float)
    if a.size == 0:
        return {'n': 0}
    return {'n': int(a.size), 'mean': round(float(a.mean()), 6),
            'sd': (None if a.size < 2 else round(float(a.std(ddof=1)), 6)),
            'min': round(float(a.min()), 6), 'max': round(float(a.max()), 6),
            'range': round(float(a.max() - a.min()), 6)}


def corr(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return {'n': int(len(x)), 'note': 'undefined (constant or too few points)'}
    return {'n': int(len(x)),
            'spearman_r': round(float(stats.spearmanr(x, y)[0]), 4),
            'spearman_p': float(stats.spearmanr(x, y)[1]),
            'pearson_r': round(float(stats.pearsonr(x, y)[0]), 4),
            'pearson_p': float(stats.pearsonr(x, y)[1]),
            'kendall_r': round(float(stats.kendalltau(x, y)[0]), 4)}


def main():
    out = {'meta': {'script': 'tools/a1_h_seed_summary.py',
                    'purpose': 'item 2 -- seed spread and the correlation contrast',
                    'seeds': SEEDS,
                    'inputs': {},
                    'timestamp_utc': datetime.now(timezone.utc).isoformat()}}

    # ------------------------------------------------------------------ gather
    runs = []          # one row per (dataset, seed)
    for ds, base_path in BASE.items():
        if ds == 'flickr30k_ref':
            continue
        for s in SEEDS:
            p = base_path if s == 42 else (SEED_JSON % (ds, s))
            if not os.path.exists(p):
                out['meta']['inputs'][p] = None
                print('MISSING %s (seed %d, %s) -- skipped' % (p, s, ds))
                continue
            out['meta']['inputs'][p] = file_sha1(p)
            d = load(p)
            r = d['result']
            fr = d['frozen']['image_only']['legacy1001']['top1_5k']
            runs.append({
                'dataset': ds, 'seed': s, 'source_json': p,
                'tag': r['tag'],
                'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                'tau3': r['image_only']['legacy1001']['tau_by_k']['3'],
                'tau10': r['image_only']['legacy1001']['tau_by_k']['10'],
                'tau20': r['image_only']['legacy1001']['tau_by_k']['20'],
                'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                'top1_50k': r.get('top1_50k_legacy1001'),
                'CG': r['CG_flickr_val'],
                'n_pairs': d['meta']['data']['n_pairs_used'],
                'n_unique_images': d['meta']['data']['n_unique_images'],
                'n_steps': d['meta']['n_steps'],
                'n_trainable_lora_params': d['meta']['n_trainable_lora_params'],
                'train_loss_epoch1': d['history'][0]['train_loss'],
                'train_loss_epoch10': d['history'][-1]['train_loss'],
                'frozen_top1_5k': fr,
                'sampling': d['meta']['data']['sampling'],
                'caption_construction': d['meta']['data']['caption_construction'],
            })
    out['runs'] = runs

    # ------------------------------------------------------------------ per-dataset spread
    per_ds = {}
    for ds in ('coco', 'food101', 'dtd'):
        rr = [r for r in runs if r['dataset'] == ds]
        per_ds[ds] = {
            'n_seeds': len(rr), 'seeds': [r['seed'] for r in rr],
            'tau5': {'per_seed': {str(r['seed']): r['tau5'] for r in rr},
                     'stats': summarise([r['tau5'] for r in rr])},
            'top1_5k': {'per_seed': {str(r['seed']): r['top1_5k'] for r in rr},
                        'stats': summarise([r['top1_5k'] for r in rr])},
            'top1_50k': {'per_seed': {str(r['seed']): r['top1_50k'] for r in rr},
                         'stats': summarise([r['top1_50k'] for r in rr])},
            'CG': {'per_seed': {str(r['seed']): r['CG'] for r in rr},
                   'stats': summarise([r['CG'] for r in rr])},
            'tau3': {'per_seed': {str(r['seed']): r['tau3'] for r in rr},
                     'stats': summarise([r['tau3'] for r in rr])},
            'tau10': {'per_seed': {str(r['seed']): r['tau10'] for r in rr},
                      'stats': summarise([r['tau10'] for r in rr])},
            'train_loss_epoch1': {'per_seed': {str(r['seed']): r['train_loss_epoch1'] for r in rr},
                                  'stats': summarise([r['train_loss_epoch1'] for r in rr])},
            'n_unique_images': {str(r['seed']): r['n_unique_images'] for r in rr},
            'sampling_identical_across_seeds': len({r['sampling'].split('seed')[0] for r in rr}) == 1,
        }
    out['per_dataset_spread'] = per_ds

    # is the seed-spread ranking of tau consistent with accuracy, per dataset?
    rank_check = {}
    for ds, v in per_ds.items():
        taus = [v['tau5']['per_seed'][str(s)] for s in v['seeds']]
        t1s = [v['top1_5k']['per_seed'][str(s)] for s in v['seeds']]
        cgs = [v['CG']['per_seed'][str(s)] for s in v['seeds']]
        rank_check[ds] = {
            'tau_rank_of_seeds': [int(x) for x in stats.rankdata([-t for t in taus]).astype(int)],
            'top1_rank_of_seeds': [int(x) for x in stats.rankdata([-t for t in t1s]).astype(int)],
            'CG_rank_of_seeds': [int(x) for x in stats.rankdata([-t for t in cgs]).astype(int)],
            'spearman_tau_vs_top1_within_dataset': (None if len(set(taus)) < 2 or len(set(t1s)) < 2
                                                    else round(float(stats.spearmanr(taus, t1s)[0]), 4)),
            'spearman_CG_vs_top1_within_dataset': (None if len(set(cgs)) < 2 or len(set(t1s)) < 2
                                                   else round(float(stats.spearmanr(cgs, t1s)[0]), 4)),
            'tau_spread': round(max(taus) - min(taus), 6),
            'top1_5k_spread': round(max(t1s) - min(t1s), 6),
            'CG_spread': round(max(cgs) - min(cgs), 6),
        }
    out['within_dataset_rank_check'] = rank_check

    # ------------------------------------------------------------------ cross-checkpoint correlations
    def cross(rows, label):
        ok = [r for r in rows if r['tau5'] is not None and r['top1_50k'] is not None]
        if len(ok) < 3:
            return {'label': label, 'n': len(ok), 'note': 'fewer than 3 usable checkpoints'}
        tau = [r['tau5'] for r in ok]
        t1 = [r['top1_50k'] for r in ok]
        t1k = [r['top1_5k'] for r in ok]
        cg = [r['CG'] for r in ok]
        return {'label': label, 'n': len(ok), 'tags': [r['tag'] for r in ok],
                'datasets': [r['dataset'] for r in ok],
                'tau5_vs_top1_50k': corr(tau, t1), 'tau5_vs_top1_5k': corr(tau, t1k),
                'CG_vs_top1_50k': corr(cg, t1), 'CG_vs_top1_5k': corr(cg, t1k),
                'tau5_range': [round(min(tau), 6), round(max(tau), 6)],
                'top1_50k_range': [round(min(t1), 6), round(max(t1), 6)]}

    seed42_only = [r for r in runs if r['seed'] == 42]
    full = list(runs)
    arch_path = 'outputs/a1_rr_e4_eval_archived.json'
    archived_rows = []
    if os.path.exists(arch_path):
        out['meta']['inputs'][arch_path] = file_sha1(arch_path)
        a = load(arch_path)
        for r in a['checkpoints']:
            if not r.get('ok'):
                continue
            archived_rows.append({
                'dataset': 'flickr30k_archived', 'seed': None, 'source_json': arch_path,
                'tag': r['tag'],
                'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                'tau3': r['image_only']['legacy1001']['tau_by_k']['3'],
                'tau10': r['image_only']['legacy1001']['tau_by_k']['10'],
                'tau20': r['image_only']['legacy1001']['tau_by_k']['20'],
                'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                'top1_50k': r.get('top1_50k_legacy1001'),
                'CG': r['CG_flickr_val'], 'n_pairs': 2000, 'n_unique_images': 400,
                'n_steps': 320, 'n_trainable_lora_params': None,
                'train_loss_epoch1': None, 'train_loss_epoch10': None,
                'frozen_top1_5k': None, 'sampling': 'archived run', 'caption_construction': 'unknown'})
    fl_ref_path = BASE['flickr30k_ref']
    fl_ref = [r for r in runs if r['dataset'] == 'flickr30k_ref']
    if os.path.exists(fl_ref_path):
        out['meta']['inputs'][fl_ref_path] = file_sha1(fl_ref_path)
        d = load(fl_ref_path)
        r = d['result']
        fl_ref = [{'dataset': 'flickr30k_ref', 'seed': 42, 'source_json': fl_ref_path,
                   'tag': r['tag'],
                   'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                   'tau3': r['image_only']['legacy1001']['tau_by_k']['3'],
                   'tau10': r['image_only']['legacy1001']['tau_by_k']['10'],
                   'tau20': r['image_only']['legacy1001']['tau_by_k']['20'],
                   'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                   'top1_50k': r.get('top1_50k_legacy1001'), 'CG': r['CG_flickr_val'],
                   'n_pairs': d['meta']['data']['n_pairs_used'],
                   'n_unique_images': d['meta']['data']['n_unique_images'],
                   'n_steps': d['meta']['n_steps'],
                   'n_trainable_lora_params': d['meta']['n_trainable_lora_params'],
                   'train_loss_epoch1': d['history'][0]['train_loss'],
                   'train_loss_epoch10': d['history'][-1]['train_loss'],
                   'frozen_top1_5k': d['frozen']['image_only']['legacy1001']['top1_5k'],
                   'sampling': d['meta']['data']['sampling'],
                   'caption_construction': d['meta']['data']['caption_construction']}]

    sets = {
        'seed42_plus_new_seeds_all': full,
        'seed42_only': seed42_only,
        'seed42_and_43': [r for r in full if r['seed'] in (42, 43)],
        'seed42_and_44': [r for r in full if r['seed'] in (42, 44)],
        'seeds43_44_only': [r for r in full if r['seed'] in (43, 44)],
        'with_flickr30k_control_seed42': seed42_only + fl_ref,
        'with_flickr30k_control_all_seeds': full + fl_ref,
        'with_archived_flickr30k_all': full + fl_ref + archived_rows,
        'controlled_trainer_plus_archived': seed42_only + fl_ref + archived_rows,
    }
    out['cross_checkpoint_correlations'] = {k: cross(v, k) for k, v in sets.items()}

    # ------------------------------------------------------------------ synthetic curve position
    curve = None
    if os.path.exists(E2):
        out['meta']['inputs'][E2] = file_sha1(E2)
        e2 = load(E2)
        conv = e2['conventions']['legacy1001']
        t1 = {c['name']: c['top1_legacy1001'] for c in e2['conditions_shared']}
        pts = []
        for lam in e2['meta']['surgery_grid']:
            if lam <= 0:
                continue
            nm = 'T%.2g' % lam
            tv = conv['tau_vs_lambda_by_k']['5']['measured'][str(lam)]
            if tv is not None:
                pts.append((float(tv), float(t1[nm]), float(lam)))
        pts.sort()
        curve = {'points_tau_ascending': [{'tau': p[0], 'top1': p[1], 'lambda': p[2]} for p in pts],
                 'tau_range': [pts[0][0], pts[-1][0]],
                 'top1_range': [min(p[1] for p in pts), max(p[1] for p in pts)]}
        out['synthetic_curve'] = curve

    def curve_pred(tau):
        if curve is None or curve['points_tau_ascending'][0]['tau'] > tau or \
                curve['points_tau_ascending'][-1]['tau'] < tau:
            return None
        pts = [(p['tau'], p['top1']) for p in curve['points_tau_ascending']]
        for i in range(len(pts) - 1):
            if pts[i][0] <= tau <= pts[i + 1][0]:
                f = 0.0 if pts[i + 1][0] == pts[i][0] else (tau - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
                return pts[i][1] + f * (pts[i + 1][1] - pts[i][1])
        return None

    pos = []
    for r in runs:
        if r['dataset'] == 'flickr30k_ref' or r['tau5'] is None:
            continue
        p = curve_pred(r['tau5'])
        pos.append({'tag': r['tag'], 'dataset': r['dataset'], 'seed': r['seed'], 'tau5': r['tau5'],
                    'top1_5k': r['top1_5k'], 'top1_50k': r['top1_50k'],
                    'synthetic_curve_top1_at_tau5': (None if p is None else round(p, 4)),
                    'excess_top1_50k': (None if p is None else round(r['top1_50k'] - p, 4)),
                    'excess_top1_5k': (None if p is None else round(r['top1_5k'] - p, 4))})
    out['synthetic_curve_position'] = pos
    ex = [p['excess_top1_50k'] for p in pos if p['excess_top1_50k'] is not None]
    out['synthetic_curve_position_summary'] = {
        'n': len(ex), 'excess_50k_mean': (round(float(np.mean(ex)), 4) if ex else None),
        'excess_50k_stats': summarise(ex)}

    # ------------------------------------------------------------------ verdict flags
    def rv(d, k):
        return d.get(k, {}).get('spearman_r') if isinstance(d.get(k), dict) else None

    cc = out['cross_checkpoint_correlations']
    out['verdict_inputs'] = {
        'full_set_spearman_tau_vs_top1_50k': rv(cc['with_flickr30k_control_all_seeds'], 'tau5_vs_top1_50k'),
        'full_set_spearman_CG_vs_top1_50k': rv(cc['with_flickr30k_control_all_seeds'], 'CG_vs_top1_50k'),
        'seed42_only_spearman_tau_vs_top1_50k': rv(cc['seed42_only'], 'tau5_vs_top1_50k'),
        'seed42_only_spearman_CG_vs_top1_50k': rv(cc['seed42_only'], 'CG_vs_top1_50k'),
        'tau_beats_CG_on_full_set': None, 'tau_beats_CG_on_seed42_only': None,
    }
    a, b = (out['verdict_inputs']['full_set_spearman_tau_vs_top1_50k'],
            out['verdict_inputs']['full_set_spearman_CG_vs_top1_50k'])
    if a is not None and b is not None:
        out['verdict_inputs']['tau_beats_CG_on_full_set'] = bool(abs(a) > abs(b))
    a, b = (out['verdict_inputs']['seed42_only_spearman_tau_vs_top1_50k'],
            out['verdict_inputs']['seed42_only_spearman_CG_vs_top1_50k'])
    if a is not None and b is not None:
        out['verdict_inputs']['tau_beats_CG_on_seed42_only'] = bool(abs(a) > abs(b))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print('== per-dataset seed spread (tau5 / top1_50k / CG) ==')
    for ds, v in per_ds.items():
        print('  %-11s tau5 %s (mean %.4f, range %.4f) | top1_50k mean %.2f range %.2f | CG mean %.4f range %.4f'
              % (ds, v['tau5']['per_seed'], v['tau5']['stats'].get('mean', float('nan')),
                 v['tau5']['stats'].get('range', float('nan')),
                 v['top1_50k']['stats'].get('mean', float('nan')),
                 v['top1_50k']['stats'].get('range', float('nan')),
                 v['CG']['stats'].get('mean', float('nan')),
                 v['CG']['stats'].get('range', float('nan'))))
    print('\n== cross-checkpoint correlations ==')
    for k, v in cc.items():
        if 'tau5_vs_top1_50k' not in v:
            print('  %-34s %s' % (k, v.get('note')))
            continue
        print('  %-34s n=%d  tau:rho=%+.4f  CG:rho=%+.4f'
              % (k, v['n'], v['tau5_vs_top1_50k'].get('spearman_r', float('nan')),
                 v['CG_vs_top1_50k'].get('spearman_r', float('nan'))))
    print('\nsaved', OUT)


if __name__ == '__main__':
    main()

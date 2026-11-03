"""A1 revision -- summary/report tables for E2/E3/E4, derived only from the a1_rr_*.json results.

Reads the experiment JSONs produced by
  tools/a1_rr_e2_topk.py        -> outputs/a1_rr_e2_topk.json
  tools/a1_rr_e3_benchmarks.py  -> outputs/a1_rr_e3_benchmarks.json
  tools/a1_rr_e4_train.py       -> outputs/a1_rr_e4_{coco,food101,dtd,flickr30k_ref}.json
                                   outputs/a1_rr_e4_eval_archived.json
and writes outputs/a1_rr_summary.json, which holds exactly the numbers quoted in
docs/A1_REVIEWER_EXPERIMENTS.md (so no headline number is typed by hand).

Also recomputes, from the E2 tau table, the Spearman correlation over the *27*-condition grid
(the archived 26 plus the extra lambda=-2 surgery condition) to test whether the published
0.9262 (outputs/a1_baseline_metrics.json, k=5) corresponds to a grid that contained lambda=-2.

Run: D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_rr_summary.py
"""
import os
import json
import glob

import numpy as np
from scipy import stats

OUT = 'outputs/a1_rr_summary.json'
E2 = 'outputs/a1_rr_e2_topk.json'
E3 = 'outputs/a1_rr_e3_benchmarks.json'
E4_MAIN = ['outputs/a1_rr_e4_coco.json', 'outputs/a1_rr_e4_food101.json',
           'outputs/a1_rr_e4_dtd.json', 'outputs/a1_rr_e4_flickr30k_ref.json']
E4_ARCHIVED = 'outputs/a1_rr_e4_eval_archived.json'
E2_LAMBDAS = ['0.0', '0.5', '1.0', '2.0']


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    out = {'meta': {'script': 'tools/a1_rr_summary.py',
                    'inputs': [p for p in [E2, E3] + E4_MAIN + [E4_ARCHIVED]
                               if os.path.exists(p)]}}

    # ---------------------------------------------------------------- E2
    e2 = load(E2)
    if e2:
        tab = {}
        for conv in ('legacy1001', 'clean1000'):
            L = e2['conventions'][conv]
            rows = {}
            for k in e2['meta']['ks']:
                ks = str(k)
                tr = L['tau_vs_lambda_by_k'][ks]
                rows[ks] = {
                    'tau': {lam: tr['measured'][lam] for lam in E2_LAMBDAS},
                    'tau_pred_exact': {lam: tr['predicted_exact'][lam] for lam in E2_LAMBDAS},
                    'spearman_tau_vs_top1_26cond': L['per_k'][ks]['spearman_tau_vs_top1_all26'],
                    'spearman_tau_vs_top1_Tfamily': L['per_k'][ks]['spearman_tau_vs_top1_Tfamily'],
                    'curve_spearman_vs_k5': L['curve_stability_vs_k5'][ks].get('spearman_vs_k5'),
                    'curve_mean_abs_diff_vs_k5': L['curve_stability_vs_k5'][ks].get('mean_abs_diff_vs_k5'),
                    'curve_max_abs_diff_vs_k5': L['curve_stability_vs_k5'][ks].get('max_abs_diff_vs_k5'),
                    'exact_predictor_mae': L['exact_predictor_error'][ks].get('mae_all_lambda'),
                    'frac_images_with_placeholder_in_topk': tr['frac_images_with_placeholder_in_topk'],
                }
            tab[conv] = rows
        sp26 = [tab['legacy1001'][str(k)]['spearman_tau_vs_top1_26cond']['r'] for k in e2['meta']['ks']
                if tab['legacy1001'][str(k)]['spearman_tau_vs_top1_26cond']['r'] ==
                tab['legacy1001'][str(k)]['spearman_tau_vs_top1_26cond']['r']]
        out['e2'] = {
            'table': tab,
            'grid26_names': e2['meta']['grid26_names'],
            'spearman_range_over_k_legacy1001': {'min': float(np.min(sp26)), 'max': float(np.max(sp26)),
                                                 'n_k': len(sp26)},
            'tau_at_lambda0.5_range': {
                'k3': tab['legacy1001']['3']['tau']['0.5'],
                'k5': tab['legacy1001']['5']['tau']['0.5'],
                'k100': tab['legacy1001']['100']['tau']['0.5'],
                'spread_k3_k100': abs(tab['legacy1001']['3']['tau']['0.5']
                                      - tab['legacy1001']['100']['tau']['0.5'])},
            'published_reference': e2['meta']['paper_reference'],
            'estimator_note': e2['meta']['tau_estimator'],
            'kendall_tau_undefined_at_k1': e2['meta']['kendall_tau_undefined_at_k1'],
        }
        # --- 27-condition variant: does including lambda=-2 reproduce the published 0.9262? ---
        conv = e2['conventions']['legacy1001']
        t1 = {c['name']: c['top1_legacy1001'] for c in e2['conditions_shared']}
        variants = {}
        for k in e2['meta']['ks']:
            taus = conv['per_k'][str(k)]['tau']
            names26 = [n for n in taus if n in set(e2['meta']['grid26_names'])]
            names27 = [n for n in taus if taus[n] is not None]
            for tag, names in (('26cond', names26), ('27cond_incl_T-2', names27)):
                v = [taus[n] for n in names if taus[n] is not None]
                tv = [t1[n] for n in names if taus[n] is not None]
                r = float(stats.spearmanr(v, tv)[0]) if len(set(v)) > 1 else None
                variants.setdefault(str(k), {})[tag] = {'r': r, 'n': len(v)}
        out['e2']['spearman_grid_variants'] = variants
        out['e2']['published_k5_spearman'] = 0.9262

    # ---------------------------------------------------------------- E3
    e3 = load(E3)
    if e3:
        rows = {}
        for key, b in e3['benchmarks'].items():
            row = {'loaded': b.get('loaded'), 'error': b.get('error')}
            if b.get('loaded') and 'variants' in b:
                row.update({'n_images': b['dataset'].get('n_raw') or b['dataset'].get('n_images'),
                            'n_classes': b.get('class_list_len'),
                            'class_selection': b['dataset'].get('class_selection')})
                for var in ('flickr30k', 'self'):
                    v = b['variants'][var]
                    row[var] = {
                        'gap_norm': v['gap_norm'],
                        'top1': {lam: v['surgery'][lam]['top1'] for lam in
                                 [str(x) for x in e3['meta']['surgery_grid']]},
                        'tau': {lam: v['surgery'][lam]['tau'] for lam in
                                [str(x) for x in e3['meta']['surgery_grid']]},
                        'tau_pred_exact': {lam: v['surgery'][lam]['tau_pred_exact'] for lam in
                                           [str(x) for x in e3['meta']['surgery_grid']]},
                        'exact_predictor_mae': v['exact_predictor_error']['mae'],
                        'exact_predictor_max_abs_err': v['exact_predictor_error']['max_abs_err'],
                        'class_contraction': v['class_contraction'],
                    }
            rows[key] = row
        out['e3'] = {'table': rows, 'meta': e3['meta']}

    # ---------------------------------------------------------------- E4
    cps = []
    for p in E4_MAIN:
        d = load(p)
        if not d:
            continue
        r = d['result']
        cps.append({'tag': r['tag'], 'trained_on': d['meta']['data']['source'],
                    'dataset': d['meta']['dataset'], 'epochs': d['meta']['epochs'],
                    'seed': d['meta']['seed'], 'steps': d['meta']['n_steps'],
                    'n_trainable_lora_params': d['meta']['n_trainable_lora_params'],
                    'n_pairs': d['meta']['data']['n_pairs_used'],
                    'n_unique_images': d['meta']['data']['n_unique_images'],
                    'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                    'tau20': r['image_only']['legacy1001']['tau_by_k']['20'],
                    'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                    'top1_50k': r.get('top1_50k_legacy1001'),
                    'CG': r['CG_flickr_val'], 'source_json': p})
    arch = load(E4_ARCHIVED)
    if arch:
        for r in arch['checkpoints']:
            if not r.get('ok'):
                cps.append({'tag': r['tag'], 'trained_on': r.get('trained_on'),
                            'error': r.get('error'), 'source_json': E4_ARCHIVED})
                continue
            cps.append({'tag': r['tag'], 'trained_on': r.get('trained_on'),
                        'dataset': 'flickr30k', 'epochs': 10, 'seed': None, 'steps': 320,
                        'n_trainable_lora_params': None, 'n_pairs': 2000, 'n_unique_images': 400,
                        'tau5': r['image_only']['legacy1001']['tau_by_k']['5'],
                        'tau20': r['image_only']['legacy1001']['tau_by_k']['20'],
                        'top1_5k': r['image_only']['legacy1001']['top1_5k'],
                        'top1_50k': r.get('top1_50k_legacy1001'),
                        'CG': r['CG_flickr_val'], 'source_json': E4_ARCHIVED})
    if cps:
        ok = [c for c in cps if 'tau5' in c and c['tau5'] is not None and c.get('top1_50k') is not None]
        out['e4'] = {'checkpoints': cps, 'n': len(cps)}
        if len(ok) >= 3:
            tau5 = [c['tau5'] for c in ok]
            t50 = [c['top1_50k'] for c in ok]
            cg = [c['CG'] for c in ok]
            out['e4']['across_checkpoints'] = {
                'n': len(ok),
                'spearman_tau5_vs_top1_50k': float(stats.spearmanr(tau5, t50)[0]),
                'pearson_tau5_vs_top1_50k': float(stats.pearsonr(tau5, t50)[0]),
                'spearman_CG_vs_top1_50k': float(stats.spearmanr(cg, t50)[0]),
                'pearson_CG_vs_top1_50k': float(stats.pearsonr(cg, t50)[0]),
                'tau5_range': [float(min(tau5)), float(max(tau5))],
                'top1_50k_range': [float(min(t50)), float(max(t50))],
                'CG_range': [float(min(cg)), float(max(cg))],
            }
        # the four controlled runs of THIS trainer (one code path, only the data changes)
        ctrl = [c for c in ok if c['dataset'] in ('coco', 'food101', 'dtd', 'flickr30k_ref')]
        if len(ctrl) >= 3:
            a = [c['tau5'] for c in ctrl]
            b = [c['top1_50k'] for c in ctrl]
            c3 = [c['CG'] for c in ctrl]
            out['e4']['across_controlled_runs'] = {
                'n': len(ctrl), 'tags': [c['tag'] for c in ctrl],
                'spearman_tau5_vs_top1_50k': float(stats.spearmanr(a, b)[0]),
                'pearson_tau5_vs_top1_50k': float(stats.pearsonr(a, b)[0]),
                'spearman_CG_vs_top1_50k': float(stats.spearmanr(c3, b)[0]),
                'pearson_CG_vs_top1_50k': float(stats.pearsonr(c3, b)[0])}

        # --- where do the checkpoints sit relative to the synthetic tau-top1 curve? ---
        if e2:
            conv = e2['conventions']['legacy1001']
            t1 = {c['name']: c['top1_legacy1001'] for c in e2['conditions_shared']}
            curve = []
            for lam in e2['meta']['surgery_grid']:
                if lam <= 0:
                    continue
                nm = 'T%.2g' % lam
                tv = conv['tau_vs_lambda_by_k']['5']['measured'][str(lam)]
                if tv is not None:
                    curve.append((float(tv), float(t1[nm]), float(lam)))
            curve.sort()                      # ascending tau
            for c in cps:
                if 'tau5' not in c or c['tau5'] is None or c['dataset'] is None:
                    continue
                t = c['tau5']
                if not (curve[0][0] <= t <= curve[-1][0]):
                    c['synthetic_curve_top1_at_tau5'] = None
                    continue
                for i in range(len(curve) - 1):
                    t0, y0, _ = curve[i]
                    t1_, y1, _ = curve[i + 1]
                    if t0 <= t <= t1_:
                        frac = 0.0 if t1_ == t0 else (t - t0) / (t1_ - t0)
                        pred = y0 + frac * (y1 - y0)
                        c['synthetic_curve_top1_at_tau5'] = round(pred, 4)
                        c['synthetic_curve_excess_top1'] = round(c['top1_5k'] - pred, 4)
                        break
            out['e4']['synthetic_curve_note'] = (
                'synthetic_curve_top1_at_tau5 linearly interpolates the ImageNet 5k T-family '
                '(lambda>0) tau->top1 curve of outputs/a1_rr_e2_topk.json (legacy1001, k=5 setup) '
                'at the checkpoint tau; synthetic_curve_excess_top1 = actual 5k top-1 minus that.')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    # ---------------------------------------------------------------- console
    if 'e2' in out:
        print('== E2 (legacy1001) ==')
        print(' k    tau(0) tau(0.5) tau(1) tau(2) rho26   curve_rho_vs_k5  predMAE  ph_in_topk')
        for k in e2['meta']['ks']:
            r = out['e2']['table']['legacy1001'][str(k)]

            def g(a):
                return ' n/a ' if r['tau'][a] is None else '%5.3f' % r['tau'][a]
            print('%-4s %s %s %s %s  %6.4f  %s  %s  %.4f'
                  % (k, g('0.0'), g('0.5'), g('1.0'), g('2.0'),
                     r['spearman_tau_vs_top1_26cond']['r'],
                     r['curve_spearman_vs_k5'], r['exact_predictor_mae'],
                     r['frac_images_with_placeholder_in_topk']))
        print(' Spearman over k (26cond): %s' % out['e2']['spearman_range_over_k_legacy1001'])
        print(' 26 vs 27-condition Spearman at k=5: %s'
              % out['e2']['spearman_grid_variants']['5'])
    if 'e3' in out:
        print('\n== E3 (flickr30k gap variant) ==')
        for key, r in out['e3']['table'].items():
            if not r.get('loaded') or 'flickr30k' not in r:
                print('%-14s LOAD/ANALYSIS FAILED: %s' % (key, r.get('error') or r.get('analysis_error')))
                continue
            v = r['flickr30k']
            print('%-14s n=%-6s C=%-4s top1(0)=%.2f | tau 0/0.5/1/2 = %s | predMAE=%s'
                  % (key, r['n_images'], r['n_classes'], v['top1']['0.0'],
                     {a: (None if v['tau'][a] is None else round(v['tau'][a], 3))
                      for a in ['0.0', '0.5', '1.0', '2.0']}, v['exact_predictor_mae']))
    if 'e4' in out:
        print('\n== E4 checkpoints ==')
        for c in out['e4']['checkpoints']:
            if 'error' in c:
                print('%-28s FAILED: %s' % (c['tag'], c['error']))
                continue
            print('%-28s tau5=%.4f top1_5k=%.2f top1_50k=%s CG=%.4f'
                  % (c['tag'], c['tau5'], c['top1_5k'], c['top1_50k'], c['CG']))
        if 'across_checkpoints' in out['e4']:
            print(' across checkpoints: %s' % out['e4']['across_checkpoints'])
    print('\nsaved', OUT)


if __name__ == '__main__':
    main()

"""Validate the item-3 (templates) and item-5 (offset) result JSONs.

Checks that the files parse, that every required key is present, that each per-image tau array has
its FULL expected length (the likely truncation mode after an unclean interruption), and that the
recorded point estimates equal the means of the stored per-image arrays.

Run: D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_validate2.py
"""
import os
import sys
import json
import numpy as np

EXPECT = {'imagenet5k': 5000, 'dtd': 1880, 'food101': 25250}
LAMBDAS = ['0.0', '0.5', '1.0', '2.0']
PER_IMAGE_LAMBDAS = ['0.5', '1.0', '2.0']
SHARD_SIG_EXPECTED = 'd13718e47e9e41c2'


def main():
    ok = True

    # ---------------- templates ----------------
    p = 'outputs/a1_h_templates.json'
    print('== %s ==' % p)
    probs = []
    d = json.load(open(p, encoding='utf-8'))
    for k in ('meta', 'results', 'stability'):
        if k not in d:
            probs.append('missing top-level key %r' % k)
    m = d.get('meta', {})
    if m.get('shard_signature') != SHARD_SIG_EXPECTED:
        probs.append('shard_signature=%r' % m.get('shard_signature'))
    if m.get('topk_for_tau') != 5:
        probs.append('topk_for_tau=%r' % m.get('topk_for_tau'))
    n_tpl = len(m.get('templates', {}))
    if n_tpl != 5:
        probs.append('expected 5 templates, found %d' % n_tpl)
    n_arr = 0
    for bname, b in d.get('results', {}).items():
        if bname not in EXPECT:
            probs.append('unexpected benchmark %r' % bname)
            continue
        if b['n_images'] != EXPECT[bname]:
            probs.append('%s n_images=%d expected %d' % (bname, b['n_images'], EXPECT[bname]))
        if len(b['templates']) != n_tpl:
            probs.append('%s has %d template rows' % (bname, len(b['templates'])))
        for tkey, tv in b['templates'].items():
            for gkey in ('coupled', 'fixed_t0'):
                sv = tv['variants'][gkey]['surgery']
                for lam in LAMBDAS:
                    if lam not in sv:
                        probs.append('%s/%s/%s missing lambda %s' % (bname, tkey, gkey, lam))
                        continue
                    arr = sv[lam].get('per_image_tau')
                    if arr is None:
                        if gkey == 'coupled' and lam in PER_IMAGE_LAMBDAS:
                            probs.append('%s/%s/%s per_image_tau missing at lambda %s'
                                         % (bname, tkey, gkey, lam))
                        continue
                    n_arr += 1
                    if len(arr) != EXPECT[bname]:
                        probs.append('%s/%s/%s/%s per_image_tau has %d entries (expected %d)'
                                     % (bname, tkey, gkey, lam, len(arr), EXPECT[bname]))
                        continue
                    a = np.asarray([np.nan if x is None else x for x in arr], dtype=float)
                    if abs(np.nanmean(a) - sv[lam]['tau']) > 1e-6:
                        probs.append('%s/%s/%s/%s mean(per_image)=%.8f != tau=%.8f'
                                     % (bname, tkey, gkey, lam, np.nanmean(a), sv[lam]['tau']))
    print('  per-image arrays checked: %d' % n_arr)
    print('  %s' % ('PASS' if not probs else 'FAIL'))
    for x in probs:
        print('      - %s' % x)
    ok &= not probs

    # ---------------- offset ----------------
    p = 'outputs/a1_h_offset.json'
    print('\n== %s ==' % p)
    probs = []
    d = json.load(open(p, encoding='utf-8'))
    for k in ('meta', 'frozen', 'synthetic_curve', 'checkpoints', 'offset_analysis'):
        if k not in d:
            probs.append('missing top-level key %r' % k)
    m = d.get('meta', {})
    if m.get('shard_signature') != SHARD_SIG_EXPECTED:
        probs.append('shard_signature=%r' % m.get('shard_signature'))
    if m.get('topk_for_tau') != 5:
        probs.append('topk_for_tau=%r' % m.get('topk_for_tau'))
    if m.get('n_sample_images') != 5000:
        probs.append('n_sample_images=%r' % m.get('n_sample_images'))
    ncurve = len(d.get('synthetic_curve', {}))
    if ncurve < 9:
        probs.append('synthetic_curve has %d points (expected >= 9)' % ncurve)
    good = bad = 0
    for r in d.get('checkpoints', []):
        if r.get('error'):
            bad += 1
            print('  checkpoint FAILED to measure: %s (%s)' % (r.get('tag'), r['error'][:80]))
            continue
        for key in ('measured', 'geometry', 'displacement', 'matched_tau',
                    'zero_vision_displacement_control', 'cg_flickr_val'):
            if key not in r:
                probs.append('%s missing %r' % (r.get('tag'), key))
        g = r.get('geometry', {})
        for key in ('within_class_spread_mean', 'margin_top1_mean', 'margin_top1_p10',
                    'mean_image_norm', 'logit_scale'):
            if key not in g:
                probs.append('%s geometry missing %r' % (r.get('tag'), key))
        dp = r.get('displacement', {})
        for key in ('mean_abs_dx', 'mean_abs_text_dx', 'component_parallel_to_gap_dir',
                    'component_orthogonal_to_gap_dir', 'frac_orthogonal_of_total'):
            if key not in dp:
                probs.append('%s displacement missing %r' % (r.get('tag'), key))
        mt = r.get('matched_tau')
        if mt:
            recomputed = mt['synthetic_lambda'] * 0  # noqa: F841  (placeholder, no arithmetic)
            if not (abs(mt['synthetic_tau'] - mt['target_tau']) < 0.003):
                probs.append('%s matched-tau residual %.5f too large'
                             % (r.get('tag'), abs(mt['synthetic_tau'] - mt['target_tau'])))
            if abs(mt['excess_top1'] - (r['measured']['top1_5k_recomputed'] - mt['synthetic_top1'])) > 1e-3:
                probs.append('%s excess_top1 inconsistent with its own inputs' % r.get('tag'))
        good += 1
    print('  checkpoints measured: %d, failed: %d, curve points: %d' % (good, bad, ncurve))
    print('  %s' % ('PASS' if not probs else 'FAIL'))
    for x in probs:
        print('      - %s' % x)
    ok &= not probs

    # ---------------- bootstrap (re-run adds templates) ----------------
    p = 'outputs/a1_h_bootstrap.json'
    print('\n== %s ==' % p)
    probs = []
    d = json.load(open(p, encoding='utf-8'))
    for k in ('meta', 'bootstrap', 'k_specificity'):
        if k not in d:
            probs.append('missing top-level key %r' % k)
    b = d.get('bootstrap', {})
    for k in ('dose_response_grid_imagenet5k_k5', 'benchmarks_e3'):
        if k not in b:
            probs.append('bootstrap missing %r' % k)
    has_tpl = 'templates' in b
    print('  templates section present: %s' % has_tpl)
    for name, conds in b.get('dose_response_grid_imagenet5k_k5', {}).get('conditions', {}).items():
        for key in ('point', 'ci_low', 'ci_high', 'se', 'n_images'):
            if key not in conds:
                probs.append('grid[%s] missing %r' % (name, key))
        if conds.get('ci_low') is not None and conds.get('ci_high') is not None:
            if not (conds['ci_low'] <= conds['point'] <= conds['ci_high']):
                probs.append('grid[%s] point outside its own CI' % name)
    for bname, e in b.get('benchmarks_e3', {}).get('benchmarks', {}).items():
        if not e.get('loaded'):
            continue
        for lam, c in e['conditions'].items():
            if not (c['ci_low'] <= c['point'] <= c['ci_high']):
                probs.append('%s lam=%s point outside its own CI' % (bname, lam))
    ks = d.get('k_specificity', {}).get('per_k_bootstrap_at_sweep_lambdas', {})
    if len(ks) < 6:
        probs.append('k_specificity has only %d k values' % len(ks))
    print('  k values bootstrapped: %s' % sorted(ks, key=int))
    print('  %s' % ('PASS' if not probs else 'FAIL'))
    for x in probs:
        print('      - %s' % x)
    ok &= not probs

    print('\nOVERALL: %s' % ('ALL PASS' if ok else 'SOME FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

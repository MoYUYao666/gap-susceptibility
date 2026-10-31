"""Validate the A1-hardening result JSONs after an unclean interruption.

Checks, per file:
  * the file parses as JSON at all (a process killed mid-write leaves a truncated file),
  * the required keys for that file type are present,
  * every per-image array has its FULL expected length (the likely truncation mode),
  * the meta block names the script, the class-list length and the shard signature,
  * the recorded statistics are internally consistent where a cheap recomputation exists
    (mean of the stored per-image tau array vs the stored scalar; 5k vs 50k top-1 plausibility).
Prints PASS/FAIL per file and exits non-zero if anything fails.

Run: D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_h_validate.py
"""
import os
import sys
import json
import glob
import hashlib
import numpy as np

EXPECT_N_SEEDS = 5000
SHARD_SIG_EXPECTED = 'd13718e47e9e41c2'
SHARD_DIR = 'data/imagenet_hf'


def shard_signature():
    parq = sorted(glob.glob(os.path.join(SHARD_DIR, '*.parquet')))
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    return h.hexdigest()[:16]


def check(cond, msg, problems):
    if not cond:
        problems.append(msg)
    return cond


def validate_seed(path, problems):
    d = json.load(open(path, encoding='utf-8'))
    for k in ('meta', 'frozen', 'history', 'result'):
        check(k in d, 'missing top-level key %r' % k, problems)
    m = d.get('meta', {})
    check(m.get('script') == 'tools/a1_h_e4_seed.py', 'meta.script=%r' % m.get('script'), problems)
    check(m.get('shard_sig') == SHARD_SIG_EXPECTED, 'shard_sig=%r' % m.get('shard_sig'), problems)
    check(m.get('n_tau_images') == EXPECT_N_SEEDS, 'n_tau_images=%r' % m.get('n_tau_images'), problems)
    # steps = 10 epochs x ceil(n_pairs/64). DTD's whole train split is 1880 images -> 300 steps;
    # every other dataset draws 2000 pairs -> 320 steps. Both are correct, not truncation.
    n_pairs = m.get('data', {}).get('n_pairs_used', 0)
    expected_steps = 10 * -(-n_pairs // 64)
    check(m.get('n_steps') == expected_steps,
          'n_steps=%r but 10 epochs x ceil(%r/64) = %d'
          % (m.get('n_steps'), n_pairs, expected_steps), problems)
    check(m.get('n_trainable_lora_params') == 491520,
          'n_trainable_lora_params=%r' % m.get('n_trainable_lora_params'), problems)
    h = d.get('history', [])
    check(len(h) == 10, 'history has %d epochs (expected 10)' % len(h), problems)
    r = d.get('result', {})
    for conv in ('legacy1001', 'clean1000'):
        io = r.get('image_only', {}).get(conv, {})
        check(io.get('top1_5k') is not None, 'result.image_only.%s.top1_5k missing' % conv, problems)
        tb = io.get('tau_by_k', {})
        for k in ('3', '5', '10', '20'):
            check(tb.get(k) is not None, 'tau_by_k[%s] missing' % k, problems)
    check(r.get('top1_50k_legacy1001') is not None, 'top1_50k_legacy1001 missing', problems)
    check(r.get('top1_50k_clean1000') is not None, 'top1_50k_clean1000 missing', problems)
    check(r.get('CG_flickr_val') is not None, 'CG_flickr_val missing', problems)
    # internal consistency: 5k and 50k top-1 must be close (same model, different sample)
    t5 = r.get('image_only', {}).get('legacy1001', {}).get('top1_5k')
    t50 = r.get('top1_50k_legacy1001')
    if t5 is not None and t50 is not None:
        check(abs(t5 - t50) < 6.0,
              '5k (%s) and 50k (%s) top-1 differ by more than 6 points' % (t5, t50), problems)
    # CG is a cosine-space distance and must be in [0, 2]
    cg = r.get('CG_flickr_val')
    if cg is not None:
        check(0.0 <= cg <= 2.0, 'CG_flickr_val=%r outside [0,2]' % cg, problems)
    return {'tag': r.get('tag'), 'seed': m.get('seed'), 'dataset': m.get('dataset'),
            'tau5': r.get('image_only', {}).get('legacy1001', {}).get('tau_by_k', {}).get('5'),
            'top1_5k': t5, 'top1_50k': t50, 'CG': cg,
            'epochs': len(h), 'ckpt': m.get('checkpoint')}


def validate_baseline(path, problems):
    d = json.load(open(path, encoding='utf-8'))
    for k in ('meta', 'conditions', 'metric_correlations', 'theory_verification',
              'estimator_crosscheck_vs_archived_scipy', 'archived_comparison', 'per_image_tau_by_condition'):
        check(k in d, 'missing top-level key %r' % k, problems)
    m = d.get('meta', {})
    check(m.get('shard_signature') == SHARD_SIG_EXPECTED,
          'shard_signature=%r' % m.get('shard_signature'), problems)
    check(m.get('class_list_len') == 1001, 'class_list_len=%r' % m.get('class_list_len'), problems)
    check(m.get('n_conditions') == 26, 'n_conditions=%r' % m.get('n_conditions'), problems)
    conds = d.get('conditions', [])
    check(len(conds) == 26, 'conditions has %d entries (expected 26)' % len(conds), problems)
    # per-image arrays must be FULL length
    pit = d.get('per_image_tau_by_condition', {})
    for kk, block in pit.items():
        for cname, arr in block.items():
            check(len(arr) == EXPECT_N_SEEDS,
                  'per_image_tau_by_condition[%s][%s] has %d entries (expected %d)'
                  % (kk, cname, len(arr), EXPECT_N_SEEDS), problems)
            a = np.asarray([np.nan if x is None else x for x in arr], dtype=float)
            # point estimate must equal the mean of the stored per-image array
            src = [c for c in conds if c['name'] == cname]
            if src and src[0].get('tau_%s' % kk) is not None:
                check(abs(np.nanmean(a) - src[0]['tau_%s' % kk]) < 1e-6,
                      'mean(per_image[%s][%s])=%.8f != stored tau=%.8f'
                      % (kk, cname, np.nanmean(a), src[0]['tau_%s' % kk]), problems)
    ksw = d.get('per_image_tau_k_sweep', {})
    check(bool(ksw), 'per_image_tau_k_sweep missing/empty', problems)
    for ks, block in ksw.get('data', {}).items():
        for cname, arr in block.items():
            check(len(arr) == EXPECT_N_SEEDS,
                  'k_sweep[%s][%s] has %d entries (expected %d)'
                  % (ks, cname, len(arr), EXPECT_N_SEEDS), problems)
    return {'n_conditions': len(conds),
            'correlations': {k: v.get('spearman_r') for k, v in d['metric_correlations'].items()},
            'per_image_arrays': sum(len(b) for b in pit.values()),
            'k_sweep_arrays': sum(len(b) for b in ksw.get('data', {}).values())}


def main():
    sig = shard_signature()
    print('live shard signature: %s (expected %s) %s'
          % (sig, SHARD_SIG_EXPECTED, 'OK' if sig == SHARD_SIG_EXPECTED else 'MISMATCH'))
    print()
    all_ok = True
    print('== seed run JSONs ==')
    for p in sorted(glob.glob('outputs/a1_h_seeds_*.json')):
        problems = []
        try:
            info = validate_seed(p, problems)
        except Exception as e:
            print('  %-46s FAIL (unreadable: %s: %s)' % (os.path.basename(p), type(e).__name__, e))
            all_ok = False
            continue
        ok = not problems
        all_ok &= ok
        print('  %-46s %s  tau5=%s top1_5k=%s top1_50k=%s CG=%s epochs=%d'
              % (os.path.basename(p), 'PASS' if ok else 'FAIL',
                 info['tau5'], info['top1_5k'], info['top1_50k'], info['CG'], info['epochs']))
        for pr in problems:
            print('        - %s' % pr)
    print()
    print('== baseline certification JSON ==')
    p = 'outputs/a1_h_baseline_metrics.json'
    problems = []
    try:
        info = validate_baseline(p, problems)
        ok = not problems
        all_ok &= ok
        print('  %-46s %s  %s' % (os.path.basename(p), 'PASS' if ok else 'FAIL', info))
        for pr in problems:
            print('        - %s' % pr)
    except Exception as e:
        print('  %-46s FAIL (unreadable: %s: %s)' % (os.path.basename(p), type(e).__name__, e))
        all_ok = False
    print()
    print('OVERALL:', 'ALL PASS' if all_ok else 'SOME FAILED -> see above')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())

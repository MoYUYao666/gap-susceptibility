"""A1 revision-material number verification (revision_additions.tex ↔ archived data).

Usage: python tools/ap3_a1_revision_check.py
Exit code: 0 = all traceable; 1 = some items do not match

Items checked:
  B1 pointwise prediction τ(λ)   <- outputs/a1_tau_holdout.json
  B2 Qwen2-VL-2B cross-arch     <- outputs/a1_qwen_surgery_v3.json
  B3 5 seeds robustness         <- outputs/a1_multiseed.json
  B4 training-time alignment dose-response <- outputs/a1_class_aligned/lr*/seed42/eval_epoch*.json
  B5 DINOv2 negative control    <- outputs/a1_dinov2_surgery.json
  B6 τ early-stopping monitor   <- outputs/a1_class_aligned/lr0.0/seed42/eval_epoch*.json
  B8 cross-family holdout generalization <- outputs/a1_tau_holdout.json
  B9 fingerprint/seed count/cross-file consistency <- outputs/a1_class_aligned/lr*/seed*/{results,eval_epoch*,tau_recomputed_ep*}.json
"""
import glob
import json
import os
import sys

OUT = 'outputs'
CLS = os.path.join(OUT, 'a1_class_aligned')
fails = []
oks = []


def j(n):
    p = os.path.join(OUT, n)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def check(label, got, want, tol):
    good = got is not None and abs(got - want) <= tol
    (oks if good else fails).append(f'{label}: data {got} vs material {want} (±{tol})')
    return good


def rd(lr, e, seed=42):
    p = os.path.join(CLS, lr, f'seed{seed}', f'eval_epoch{e}.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


print('=== B1 pointwise prediction τ(λ) ===')
d = j('a1_tau_holdout.json')
t = d['theory_vs_measured_tau']['predicted_tau_exact_vs_measured_tau_5k']
check('B1 n', t['n'], 9, 0)
check('B1 max abs error', t['max_abs_diff'], 0.0019, 1e-9)
print(f"  n={t['n']} pearson={t['pearson_r']} max_abs_diff={t['max_abs_diff']} identical={t['identical']}")

print('=== B2 Qwen2-VL-2B per λ ===')
q = j('a1_qwen_surgery_v3.json')
by = {r['lambda']: r for r in q['results']}
for lam, tau, top1, cg in ((0.25, 0.815, 16.7, 0.716), (0.5, 0.683, 16.7, 0.511),
                           (1.0, 0.482, 15.3, 0.155), (2.0, 0.271, 8.3, 0.613)):
    r = by.get(lam)
    if not r:
        fails.append(f'B2 λ={lam} missing data')
        continue
    check(f'B2 λ={lam} image τ', r['image_side']['tau'], tau, 0.001)
    check(f'B2 λ={lam} image top1', r['image_side']['top1'], top1, 0.06)
    check(f'B2 λ={lam} image CG', r['image_side']['CG'], cg, 0.001)
    check(f'B2 λ={lam} text τ', r['text_side']['tau'], 1.0, 1e-9)
check('B2 frozen top1', q['frozen']['top1'], 17.1, 0.06)
check('B2 frozen CG', q['frozen']['CG'], 0.867, 0.001)

print('=== B3 5 seeds robustness ===')
m = j('a1_multiseed.json')['aggregate']['spearman']
for k, mean, std in (('tau', 0.9167, 0.0064), ('mean_cos', 0.8672, 0.0046),
                     ('cka', 0.7781, 0.0209), ('CG', -0.1313, 0.0285)):
    check(f'B3 {k} mean', m[k]['mean'], mean, 5e-5)
    check(f'B3 {k} std', m[k]['std'], std, 5e-5)

print('=== B4 dose-response (λ_reg 0→1; seed42 endpoints + three-seed mean) ===')


def tau_rec(lam_dir, seed=42, ep=10):
    p = os.path.join(CLS, lam_dir, 'seed%d' % seed, 'tau_recomputed_ep%d.json' % (ep))
    return json.load(open(p, encoding='utf-8'))['tau_final'] if os.path.exists(p) else None


def res(lam_dir, seed=42):
    p = os.path.join(CLS, lam_dir, 'seed%d' % seed, 'results.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


lo, hi = res('lr0.0'), res('lr1.0')
check('B4 top-1 start point(seed42)', lo['top1_50k'], 58.08, 0.06)
check('B4 top-1 end point(seed42)', hi['top1_50k'], 55.49, 0.06)
check('B4 τ start point(seed42)', tau_rec('lr0.0'), 0.7088, 0.0006)
check('B4 τ end point(seed42)', tau_rec('lr1.0'), 0.6397, 0.0006)
check('B4 val start point(seed42)', lo['val_loss'], 2.3591, 0.005)
check('B4 val end point(seed42)', hi['val_loss'], 2.1348, 0.005)
for lam_dir, t1, tau_m, vl in (('lr0.0', 58.11, 0.7079, 2.3284),
                               ('lr1.0', 55.60, 0.6352, 2.1240)):
    ts, taus, vs = [], [], []
    for s in (42, 123, 456):
        rp = os.path.join(CLS, lam_dir, 'seed%d' % s, 'results.json')
        if os.path.exists(rp):
            r = json.load(open(rp, encoding='utf-8'))
            ts.append(r['top1_50k'])
            vs.append(r['val_loss'])
        tv = tau_rec(lam_dir, s)
        if tv is not None:
            taus.append(tv)
    check('B4 %s top-1 three-seed mean(n=%d)' % (lam_dir, len(ts)), sum(ts) / len(ts), t1, 0.02)
    check('B4 %s τ three-seed mean(n=%d)' % (lam_dir, len(taus)), sum(taus) / len(taus), tau_m, 0.001)
    check('B4 %s val three-seed mean(n=%d)' % (lam_dir, len(vs)), sum(vs) / len(vs), vl, 0.002)

print('=== B5 DINOv2 ===')
dv = j('a1_dinov2_surgery.json')
alltau, alltop = [], []
for r in dv['results']:
    for k, v in r.items():
        if isinstance(v, dict) and 'tau' in v:
            alltau.append(v['tau'])
            alltop.append(v['top1'])
check('B5 frozen CG', dv['frozen']['CG'], 0.043, 0.001)
check('B5 frozen top1', dv['frozen']['top1'], 48.2, 0.01)
check('B5 top-1 lower bound', min(alltop), 48.18, 0.005)
check('B5 top-1 upper bound', max(alltop), 48.26, 0.005)
print(f"  τ min {min(alltau):.4f} (material claims '>0.93' → actually {'holds but only by 0.0001' if min(alltau) > 0.93 else 'does not hold'})")

print('=== B6 τ early stopping (lr0.0 per epoch) ===')
ref = {1: (0.7563, 59.79, 2.3383), 2: (0.7386, 59.34, 2.3233), 3: (0.7270, 58.87, 2.3101),
       5: (0.7109, 58.28, 2.3479), 10: (0.7088, 58.08, 2.3591)}
# Note: ep10's val_loss uses the training-time record (results.json = 2.35905), same source as block
#     4's three-seed mean; eval_epoch10.json records 2.36417 from re-evaluating reloaded weights, Δ=0.005 (X.5).
for e, (tau, top1, val) in ref.items():
    d = rd('lr0.0', e)
    if not d:
        fails.append(f'B6 epoch{e} missing data')
        continue
    check(f'B6 epoch{e} τ', d['tau_final'], tau, 0.0006)
    check(f'B6 epoch{e} top-1', d['top1_50k'], top1, 0.06)
    # ep10's val_loss uses the training-time record (same source as block 4's three-seed mean);
    # the other epochs come from the per-epoch re-evaluation. The two differ by 0.005 for the same run (A1_REVISION_REAUDIT X.5).
    v = res('lr0.0')['val_loss'] if e == 10 else d['val_loss']
    check(f'B6 epoch{e} val_loss', v, val, 0.0006)

print('=== B8 cross-family holdout generalization ===')
lo_ = j('a1_tau_holdout.json')['leave_one_model_out']
check('B8 clip R²', lo_['clip']['tau_predictor']['r2_holdout'], 0.371, 0.001)
check('B8 siglip R²', lo_['siglip']['tau_predictor']['r2_holdout'], 0.378, 0.001)
sp = j('a1_tau_holdout.json')['pooled_predictors']
check('B8 pooled τ ρ', sp['tau']['spearman_r'], 0.927, 0.001)
check('B8 pooled CG ρ', sp['CG']['spearman_r'], -0.251, 0.001)

print('=== B9 data fingerprint and cross-file consistency ===')
SWEEP = ('lr0.0', 'lr0.05', 'lr0.1', 'lr0.25', 'lr0.5', 'lr1.0')
LAM_TXT = {'lr0.0': '0.0', 'lr0.05': '0.05', 'lr0.1': '0.1',
           'lr0.25': '0.25', 'lr0.5': '0.5', 'lr1.0': '1.0'}
SEEDS3 = ('lr0.0', 'lr0.1', 'lr0.5', 'lr1.0')   # material cites these as "three-seed mean"
SEEDS1 = ('lr0.05', 'lr0.25')                   # material cites only seed42 for the intermediate points


def jfile(path):
    """Fault-tolerant JSON read: missing/corrupt/non-object all give None (caller records FAIL, no exception)."""
    try:
        with open(path, encoding='utf-8') as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def fnum(v):
    """Accept only real numbers; None/strings/booleans all give None."""
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def seeds_hit(lr):
    """Seed numbers with a results.json present under that λ directory (ascending; parse failure gives -1)."""
    got = []
    for p in glob.glob(os.path.join(CLS, lr, 'seed*', 'results.json')):
        try:
            got.append(int(os.path.basename(os.path.dirname(p))[4:]))
        except ValueError:
            got.append(-1)
    return sorted(got)


def seed_mean(lr, fname, key, seeds=(42, 123, 456)):
    """Three-seed mean; if seeds are missing, average the existing files (the seed count itself is pinned by B9.2)."""
    vals = []
    for s in seeds:
        d = jfile(os.path.join(CLS, lr, 'seed%d' % s, fname)) or {}
        v = fnum(d.get(key))
        if v is not None:
            vals.append(v)
    return sum(vals) / len(vals) if vals else None


def mono(series, label):
    """Strictly decreasing across adjacent λ points; missing/inverted values always FAIL (all go through check, counts stay consistent)."""
    miss = [lr for lr in SWEEP if series.get(lr) is None]
    if miss:
        fails.append('B9 monotonic %s missing data: %s' % (label, ', '.join(miss)))
        return
    for a, b in zip(SWEEP, SWEEP[1:]):
        check('B9 monotonic %s λ=%s→%s' % (label, LAM_TXT[a], LAM_TXT[b]),
              1.0 if series[b] < series[a] else 0.0, 1.0, 0)


# B9.1 fingerprint/provenance: 1000 classes + globally unique parquet signature (1001-class contamination fails here)
res_files = sorted(glob.glob(os.path.join(CLS, 'lr*', 'seed*', 'results.json')))
sigs, cls_bad, fp_bad, meta_bad = set(), 0, 0, 0
for p in res_files:
    d = jfile(p) or {}
    fp = d.get('fingerprint')
    if not isinstance(fp, dict):
        fp_bad += 1
        cls_bad += 1
        continue
    if fp.get('class_names') != 1000:
        cls_bad += 1
    s = fp.get('parquet_sig')
    if isinstance(s, str) and s:
        sigs.add(s)
    else:
        fp_bad += 1
    lr = os.path.basename(os.path.dirname(os.path.dirname(p)))
    try:
        want_lam = float(lr[2:].split('_')[0])
        want_seed = int(os.path.basename(os.path.dirname(p))[4:])
    except ValueError:
        meta_bad += 1
        continue
    if fnum(d.get('lambda_reg')) != want_lam or fnum(d.get('seed')) != want_seed:
        meta_bad += 1
check('B9 results.json fingerprint coverage count ≥ 14', 1.0 if len(res_files) >= 14 else 0.0, 1.0, 0)
check('B9 results.json files missing fingerprint fields', float(fp_bad), 0.0, 0)
check('B9 files with fingerprint.class_names != 1000', float(cls_bad), 0.0, 0)
check('B9 fingerprint.parquet_sig distinct count', float(len(sigs)), 1.0, 0)
check('B9 files whose in-file λ/seed declaration disagrees with the directory', float(meta_bad), 0.0, 0)
print('  results.json %d files, parquet_sig=%s (unique), class_names=1000, deviations %d'
      % (len(res_files), '/'.join(sorted(sigs)) or 'missing', cls_bad))

# B9.2 seed count: λ∈{0,0.1,0.5,1.0} have 3 each (42/123/456); λ∈{0.05,0.25} have 1 each (42)
for lr in SEEDS3:
    got = seeds_hit(lr)
    check('B9 %s three-seed point results.json count' % lr, float(len(got)), 3.0, 0)
    check('B9 %s seed set = [42,123,456]' % lr, 1.0 if got == [42, 123, 456] else 0.0, 1.0, 0)
for lr in SEEDS1:
    got = seeds_hit(lr)
    check('B9 %s intermediate point results.json count (single seed)' % lr, float(len(got)), 1.0, 0)
    check('B9 %s seed set = [42]' % lr, 1.0 if got == [42] else 0.0, 1.0, 0)
print('  n=3: %s;n=1: %s'
      % (' '.join('%s:%d' % (lr, len(seeds_hit(lr))) for lr in SEEDS3),
         ' '.join('%s:%d' % (lr, len(seeds_hit(lr))) for lr in SEEDS1)))

# B9.3 λ=0/seed42 endpoint: the two authoritative files must agree, and the material cites the training-time record
r0 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'results.json'))
e10 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch10.json'))
if r0 is None or e10 is None:
    fails.append('B9 λ=0/seed42 endpoint missing files (results.json / eval_epoch10.json)')
else:
    t_r, t_e = fnum(r0.get('top1_50k')), fnum(e10.get('top1_50k'))
    v_r, v_e = fnum(r0.get('val_loss')), fnum(e10.get('val_loss'))
    if None in (t_r, t_e, v_r, v_e):
        fails.append('B9 λ=0/seed42 endpoint missing top1_50k/val_loss fields')
    else:
        dval = abs(v_r - v_e)
        check('B9 λ0/seed42 top1_50k identical across files', abs(t_r - t_e), 0.0, 0)
        check('B9 λ0/seed42 val_loss cross-file diff < 0.01', dval, 0.0, 0.00999)
        check('B9 material ep10 val_loss 2.3591 = training-time record', v_r, 2.3591, 0.0006)
        check('B9 material value 2.3591 is closer to the training-time record than to the re-eval record',
              1.0 if abs(v_r - 2.3591) < abs(v_e - 2.3591) else 0.0, 1.0, 0)
        print('  λ=0/seed42 top1_50k %.6f == %.6f; val_loss training-time %.7f vs re-eval %.7f, Δ=%.7f'
              % (t_r, t_e, v_r, v_e, dval))

# B9.4 monotonicity: τ↓ / zero-shot top-1↓ / val_loss↓
#   (a) all six seed42 points monotone — the material claims a monotone response over λ=0→1, and
#       the intermediate points (0.05/0.25) only have seed42;
#   (b) four three-seed mean points (0/0.1/0.5/1) monotone — the material actually cites these four
#       points' 58.11→55.60 / 0.708→0.635 / 2.33→2.12. The two conventions are asserted separately.
tau42, top42, val42 = {}, {}, {}
for lr in SWEEP:
    t = jfile(os.path.join(CLS, lr, 'seed42', 'tau_recomputed_ep10.json')) or {}
    r = jfile(os.path.join(CLS, lr, 'seed42', 'results.json')) or {}
    tau42[lr] = fnum(t.get('tau_final'))
    top42[lr] = fnum(r.get('top1_50k'))
    val42[lr] = fnum(r.get('val_loss'))
mono(tau42, 'τ(seed42,ep10)')
mono(top42, 'zero-shot top-1(seed42)')
mono(val42, 'val_loss(seed42)')
tau_m = {lr: seed_mean(lr, 'tau_recomputed_ep10.json', 'tau_final') for lr in SWEEP}
top_m = {lr: seed_mean(lr, 'results.json', 'top1_50k') for lr in SWEEP}
val_m = {lr: seed_mean(lr, 'results.json', 'val_loss') for lr in SWEEP}
for series, label in ((tau_m, 'τ(three-seed mean)'), (top_m, 'zero-shot top-1(three-seed mean)'),
                      (val_m, 'val_loss(three-seed mean)')):
    if any(series.get(lr) is None for lr in SEEDS3):
        fails.append('B9 mean %s missing data' % label)
        continue
    check('B9 mean %s strictly decreasing across the four three-seed points' % label,
          1.0 if all(series[b] < series[a] for a, b in zip(SEEDS3, SEEDS3[1:])) else 0.0, 1.0, 0)


def seq(series):
    return ' > '.join('%.4f' % series[lr] if series.get(lr) is not None else 'NA' for lr in SWEEP)


print('  seed42  τ    ' + seq(tau42))
print('  seed42  top1 ' + seq(top42))
print('  seed42  val  ' + seq(val42))
print('  mean(4 points) τ    ' + ' > '.join('%.4f' % tau_m[lr] for lr in SEEDS3))
print('  mean(4 points) top1 ' + ' > '.join('%.4f' % top_m[lr] for lr in SEEDS3))
print('  mean(4 points) val  ' + ' > '.join('%.4f' % val_m[lr] for lr in SEEDS3))
print('  Note: reading the three-seed means mixed with single-seed intermediate points as one val series (%s) produces at λ=0→0.05'
      % seq(val_m))
print('      a "reversal" 2.3284<2.3376; this is a mix of conventions (3-seed mean vs single seed), and the material does not read it that way;')
print('      the six-point monotonicity is carried by the seed42 series, and mean monotonicity is asserted only on the four three-seed points.')

# B9.5 derived percentages: τ erosion from ep1→ep10 is -6.3%, zero-shot top-1 erosion -2.9%
e1 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch1.json'))
if e1 is None:
    fails.append('B9 lr0.0/seed42/eval_epoch1.json missing file (derived percentages)')
else:
    tau1, tau10 = fnum(e1.get('tau_final')), (fnum(e10.get('tau_final')) if e10 else None)
    p1, p10 = fnum(e1.get('top1_50k')), (fnum(e10.get('top1_50k')) if e10 else None)
    if None in (tau1, tau10, p1, p10):
        fails.append('B9 ep1/ep10 missing τ/top1 fields (derived percentages)')
    else:
        rel_tau = (tau10 - tau1) / tau1 * 100.0
        rel_top = (p10 - p1) / p1 * 100.0
        check('B9 τ ep1→ep10 relative change %', rel_tau, -6.3, 0.05)
        check('B9 top-1 ep1→ep10 relative change %', rel_top, -2.9, 0.05)
        check('B9 |τ erosion| > |top-1 erosion|', 1.0 if abs(rel_tau) > abs(rel_top) else 0.0, 1.0, 0)
        print('  ep1→ep10 τ %.7f→%.7f = %.4f%%;top-1 %.3f→%.3f = %.4f%%'
              % (tau1, tau10, rel_tau, p1, p10, rel_top))

# B9.6 val_loss minimum location: argmin = epoch 3, and epoch 10 is the max of the five points
vals_ep = {}
for e in (1, 2, 3, 5, 10):
    d = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch%d.json' % e))
    v = fnum((d or {}).get('val_loss'))
    if v is None:
        fails.append('B9 lr0.0/seed42/eval_epoch%d.json missing val_loss' % e)
        continue
    vals_ep[e] = v
if len(vals_ep) == 5:
    check('B9 val_loss argmin = epoch 3', float(min(vals_ep, key=vals_ep.get)), 3.0, 0)
    check('B9 val_loss max = epoch 10', float(max(vals_ep, key=vals_ep.get)), 10.0, 0)
    alt = dict(vals_ep)
    v_r0 = fnum((r0 or {}).get('val_loss'))
    if v_r0 is not None:
        alt[10] = v_r0
        check('B9 after switching to the training-time ep10 value argmin is still = epoch 3',
              float(min(alt, key=alt.get)), 3.0, 0)
        check('B9 after switching to the training-time ep10 value max is still = epoch 10',
              float(max(alt, key=alt.get)), 10.0, 0)
    print('  per-epoch val_loss ' + ', '.join('ep%d %.6f' % (e, v) for e, v in sorted(vals_ep.items())))

# B9.7 per-sample τ spread: material interval 0.26–0.28 (after re-evaluation; the old draft's 0.32 does not hold)
sds = {}
for e in (1, 2, 3, 5, 10):
    d = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'tau_recomputed_ep%d.json' % e))
    v = fnum((d or {}).get('tau_sd_across_samples'))
    if v is None:
        fails.append('B9 lr0.0/seed42/tau_recomputed_ep%d.json missing tau_sd_across_samples' % e)
        continue
    sds[e] = v
if sds:
    sd_lo, sd_hi = min(sds.values()), max(sds.values())
    check('B9 per-sample τ sd lower bound(ep1)', sd_lo, 0.2557, 0.0006)
    check('B9 per-sample τ sd upper bound(ep10)', sd_hi, 0.2822, 0.0006)
    check('B9 material sd interval = 0.26–0.28', 1.0 if (round(sd_lo, 2) == 0.26 and round(sd_hi, 2) == 0.28) else 0.0, 1.0, 0)
    print('  per-epoch sd ' + ', '.join('ep%d %.6f' % (e, v) for e, v in sorted(sds.items())))

# B9.8 τ recomputation provenance: all from the 5000-image subsample referenced by the cache
tr_files = sorted(glob.glob(os.path.join(CLS, 'lr*', 'seed*', 'tau_recomputed_ep*.json')))
src_bad = 0
for p in tr_files:
    d = jfile(p) or {}
    if d.get('sub_indices_source') != 'cache' or fnum(d.get('n_samples')) != 5000.0:
        src_bad += 1
check('B9 τ recomputation file coverage ≥ 14', 1.0 if len(tr_files) >= 14 else 0.0, 1.0, 0)
check('B9 anomalous τ recomputation provenance count(sub_indices_source/n_samples)', float(src_bad), 0.0, 0)
print('  τ recomputation files %d: sub_indices_source=cache, n_samples=5000, anomalous %d'
      % (len(tr_files), src_bad))

print()
print(f'passed {len(oks)} items, failed {len(fails)} items')
for f in fails:
    print('  FAIL', f)
sys.exit(0 if not fails else 1)

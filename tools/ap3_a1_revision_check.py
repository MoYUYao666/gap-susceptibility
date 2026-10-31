"""A1 返修素材数字核对（revision_additions.tex ↔ 归档数据）。

用法： python tools/ap3_a1_revision_check.py
退出码：0 = 全部可溯源；1 = 有对不上的项

核对项：
  B1 逐点预测 τ(λ)        <- outputs/a1_tau_holdout.json
  B2 Qwen2-VL-2B 跨架构    <- outputs/a1_qwen_surgery_v3.json
  B3 5 seeds 稳健          <- outputs/a1_multiseed.json
  B4 训练期对齐剂量-响应    <- outputs/a1_class_aligned/lr*/seed42/eval_epoch*.json
  B5 DINOv2 阴性对照        <- outputs/a1_dinov2_surgery.json
  B6 τ 早停监控            <- outputs/a1_class_aligned/lr0.0/seed42/eval_epoch*.json
  B8 跨族留出泛化           <- outputs/a1_tau_holdout.json
  B9 指纹/种子数/跨文件自洽  <- outputs/a1_class_aligned/lr*/seed*/{results,eval_epoch*,tau_recomputed_ep*}.json
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
    (oks if good else fails).append(f'{label}: 数据 {got} vs 素材 {want} (±{tol})')
    return good


def rd(lr, e, seed=42):
    p = os.path.join(CLS, lr, f'seed{seed}', f'eval_epoch{e}.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


print('=== B1 逐点预测 τ(λ) ===')
d = j('a1_tau_holdout.json')
t = d['theory_vs_measured_tau']['predicted_tau_exact_vs_measured_tau_5k']
check('B1 n', t['n'], 9, 0)
check('B1 最大绝对误差', t['max_abs_diff'], 0.0019, 1e-9)
print(f"  n={t['n']} pearson={t['pearson_r']} max_abs_diff={t['max_abs_diff']} identical={t['identical']}")

print('=== B2 Qwen2-VL-2B 逐 λ ===')
q = j('a1_qwen_surgery_v3.json')
by = {r['lambda']: r for r in q['results']}
for lam, tau, top1, cg in ((0.25, 0.815, 16.7, 0.716), (0.5, 0.683, 16.7, 0.511),
                           (1.0, 0.482, 15.3, 0.155), (2.0, 0.271, 8.3, 0.613)):
    r = by.get(lam)
    if not r:
        fails.append(f'B2 λ={lam} 缺数据')
        continue
    check(f'B2 λ={lam} image τ', r['image_side']['tau'], tau, 0.001)
    check(f'B2 λ={lam} image top1', r['image_side']['top1'], top1, 0.06)
    check(f'B2 λ={lam} image CG', r['image_side']['CG'], cg, 0.001)
    check(f'B2 λ={lam} text τ', r['text_side']['tau'], 1.0, 1e-9)
check('B2 frozen top1', q['frozen']['top1'], 17.1, 0.06)
check('B2 frozen CG', q['frozen']['CG'], 0.867, 0.001)

print('=== B3 5 seeds 稳健 ===')
m = j('a1_multiseed.json')['aggregate']['spearman']
for k, mean, std in (('tau', 0.9167, 0.0064), ('mean_cos', 0.8672, 0.0046),
                     ('cka', 0.7781, 0.0209), ('CG', -0.1313, 0.0285)):
    check(f'B3 {k} mean', m[k]['mean'], mean, 5e-5)
    check(f'B3 {k} std', m[k]['std'], std, 5e-5)

print('=== B4 剂量-响应（λ_reg 0→1；seed42 端点 + 三种子均值）===')


def tau_rec(lam_dir, seed=42, ep=10):
    p = os.path.join(CLS, lam_dir, 'seed%d' % seed, 'tau_recomputed_ep%d.json' % (ep))
    return json.load(open(p, encoding='utf-8'))['tau_final'] if os.path.exists(p) else None


def res(lam_dir, seed=42):
    p = os.path.join(CLS, lam_dir, 'seed%d' % seed, 'results.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


lo, hi = res('lr0.0'), res('lr1.0')
check('B4 top-1 起点(seed42)', lo['top1_50k'], 58.08, 0.06)
check('B4 top-1 终点(seed42)', hi['top1_50k'], 55.49, 0.06)
check('B4 τ 起点(seed42)', tau_rec('lr0.0'), 0.7088, 0.0006)
check('B4 τ 终点(seed42)', tau_rec('lr1.0'), 0.6397, 0.0006)
check('B4 val 起点(seed42)', lo['val_loss'], 2.3591, 0.005)
check('B4 val 终点(seed42)', hi['val_loss'], 2.1348, 0.005)
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
    check('B4 %s top-1 三种子均值(n=%d)' % (lam_dir, len(ts)), sum(ts) / len(ts), t1, 0.02)
    check('B4 %s τ 三种子均值(n=%d)' % (lam_dir, len(taus)), sum(taus) / len(taus), tau_m, 0.001)
    check('B4 %s val 三种子均值(n=%d)' % (lam_dir, len(vs)), sum(vs) / len(vs), vl, 0.002)

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
check('B5 top-1 下界', min(alltop), 48.18, 0.005)
check('B5 top-1 上界', max(alltop), 48.26, 0.005)
print(f"  τ 最小 {min(alltau):.4f}（素材称 '>0.93' → 实际 {'成立但仅高 0.0001' if min(alltau) > 0.93 else '不成立'}）")

print('=== B6 τ 早停（lr0.0 逐 epoch）===')
ref = {1: (0.7563, 59.79, 2.3383), 2: (0.7386, 59.34, 2.3233), 3: (0.7270, 58.87, 2.3101),
       5: (0.7109, 58.28, 2.3479), 10: (0.7088, 58.08, 2.3591)}
# 注：ep10 的 val_loss 取训练时记录（results.json = 2.35905），与块 4 的三种子均值同源；
#     eval_epoch10.json 记的是重载权重后复评的 2.36417，两者差 0.005（见 A1_REVISION_REAUDIT X.5）。
for e, (tau, top1, val) in ref.items():
    d = rd('lr0.0', e)
    if not d:
        fails.append(f'B6 epoch{e} 缺数据')
        continue
    check(f'B6 epoch{e} τ', d['tau_final'], tau, 0.0006)
    check(f'B6 epoch{e} top-1', d['top1_50k'], top1, 0.06)
    # ep10 的 val_loss 以训练时记录为准（与块 4 的三种子均值同源）；
    # 其余 epoch 来自逐 epoch 复评。两者对同一次运行差 0.005（A1_REVISION_REAUDIT X.5）。
    v = res('lr0.0')['val_loss'] if e == 10 else d['val_loss']
    check(f'B6 epoch{e} val_loss', v, val, 0.0006)

print('=== B8 跨族留出泛化 ===')
lo_ = j('a1_tau_holdout.json')['leave_one_model_out']
check('B8 clip R²', lo_['clip']['tau_predictor']['r2_holdout'], 0.371, 0.001)
check('B8 siglip R²', lo_['siglip']['tau_predictor']['r2_holdout'], 0.378, 0.001)
sp = j('a1_tau_holdout.json')['pooled_predictors']
check('B8 pooled τ ρ', sp['tau']['spearman_r'], 0.927, 0.001)
check('B8 pooled CG ρ', sp['CG']['spearman_r'], -0.251, 0.001)

print('=== B9 数据指纹与跨文件一致性 ===')
SWEEP = ('lr0.0', 'lr0.05', 'lr0.1', 'lr0.25', 'lr0.5', 'lr1.0')
LAM_TXT = {'lr0.0': '0.0', 'lr0.05': '0.05', 'lr0.1': '0.1',
           'lr0.25': '0.25', 'lr0.5': '0.5', 'lr1.0': '1.0'}
SEEDS3 = ('lr0.0', 'lr0.1', 'lr0.5', 'lr1.0')   # 素材按“三种子均值”引用
SEEDS1 = ('lr0.05', 'lr0.25')                   # 中间点素材只引用 seed42


def jfile(path):
    """容错读 JSON：缺失/损坏/非对象一律 None（由调用方记 FAIL，不抛异常）。"""
    try:
        with open(path, encoding='utf-8') as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def fnum(v):
    """只接受真数值；None/字符串/布尔一律 None。"""
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def seeds_hit(lr):
    """该 λ 目录下存在 results.json 的 seed 号（升序；目录名解析失败记 -1）。"""
    got = []
    for p in glob.glob(os.path.join(CLS, lr, 'seed*', 'results.json')):
        try:
            got.append(int(os.path.basename(os.path.dirname(p))[4:]))
        except ValueError:
            got.append(-1)
    return sorted(got)


def seed_mean(lr, fname, key, seeds=(42, 123, 456)):
    """三种子均值；缺种子则由现存文件求均值（种子数本身由 B9.2 单独卡住）。"""
    vals = []
    for s in seeds:
        d = jfile(os.path.join(CLS, lr, 'seed%d' % s, fname)) or {}
        v = fnum(d.get(key))
        if v is not None:
            vals.append(v)
    return sum(vals) / len(vals) if vals else None


def mono(series, label):
    """相邻 λ 点严格递减；缺值/反转一律 FAIL（全部经 check，计数保持一致）。"""
    miss = [lr for lr in SWEEP if series.get(lr) is None]
    if miss:
        fails.append('B9 单调 %s 缺数据: %s' % (label, ', '.join(miss)))
        return
    for a, b in zip(SWEEP, SWEEP[1:]):
        check('B9 单调 %s λ=%s→%s' % (label, LAM_TXT[a], LAM_TXT[b]),
              1.0 if series[b] < series[a] else 0.0, 1.0, 0)


# B9.1 指纹/溯源：类数 1000 + 全树唯一 parquet 签名（1001 类污染在此 FAIL）
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
check('B9 results.json 指纹覆盖数 ≥ 14', 1.0 if len(res_files) >= 14 else 0.0, 1.0, 0)
check('B9 指纹字段缺失的 results.json 数', float(fp_bad), 0.0, 0)
check('B9 fingerprint.class_names 非 1000 的文件数', float(cls_bad), 0.0, 0)
check('B9 fingerprint.parquet_sig 去重后数量', float(len(sigs)), 1.0, 0)
check('B9 文件内 λ/seed 声明与目录不符的文件数', float(meta_bad), 0.0, 0)
print('  results.json %d 个，parquet_sig=%s（唯一），class_names=1000，偏离 %d 个'
      % (len(res_files), '/'.join(sorted(sigs)) or '缺失', cls_bad))

# B9.2 种子数：λ∈{0,0.1,0.5,1.0} 各 3（42/123/456）；λ∈{0.05,0.25} 各 1（42）
for lr in SEEDS3:
    got = seeds_hit(lr)
    check('B9 %s 三种子点 results.json 数' % lr, float(len(got)), 3.0, 0)
    check('B9 %s 种子集合 = [42,123,456]' % lr, 1.0 if got == [42, 123, 456] else 0.0, 1.0, 0)
for lr in SEEDS1:
    got = seeds_hit(lr)
    check('B9 %s 中间点 results.json 数（单种子）' % lr, float(len(got)), 1.0, 0)
    check('B9 %s 种子集合 = [42]' % lr, 1.0 if got == [42] else 0.0, 1.0, 0)
print('  n=3: %s；n=1: %s'
      % (' '.join('%s:%d' % (lr, len(seeds_hit(lr))) for lr in SEEDS3),
         ' '.join('%s:%d' % (lr, len(seeds_hit(lr))) for lr in SEEDS1)))

# B9.3 λ=0/seed42 端点：两个权威文件必须自洽，且素材引用训练期记录
r0 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'results.json'))
e10 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch10.json'))
if r0 is None or e10 is None:
    fails.append('B9 λ=0/seed42 端点缺文件（results.json / eval_epoch10.json）')
else:
    t_r, t_e = fnum(r0.get('top1_50k')), fnum(e10.get('top1_50k'))
    v_r, v_e = fnum(r0.get('val_loss')), fnum(e10.get('val_loss'))
    if None in (t_r, t_e, v_r, v_e):
        fails.append('B9 λ=0/seed42 端点缺 top1_50k/val_loss 字段')
    else:
        dval = abs(v_r - v_e)
        check('B9 λ0/seed42 top1_50k 跨文件完全一致', abs(t_r - t_e), 0.0, 0)
        check('B9 λ0/seed42 val_loss 跨文件差 < 0.01', dval, 0.0, 0.00999)
        check('B9 素材 ep10 val_loss 2.3591 = 训练期记录', v_r, 2.3591, 0.0006)
        check('B9 素材值 2.3591 更近训练期记录而非复评记录',
              1.0 if abs(v_r - 2.3591) < abs(v_e - 2.3591) else 0.0, 1.0, 0)
        print('  λ=0/seed42 top1_50k %.6f == %.6f；val_loss 训练期 %.7f vs 复评 %.7f，Δ=%.7f'
              % (t_r, t_e, v_r, v_e, dval))

# B9.4 单调性：τ↓ / zero-shot top-1↓ / val_loss↓
#   (a) seed42 六点全程单调——素材称响应在 λ=0→1 上单调，中间点(0.05/0.25)只有 seed42；
#   (b) 三种子均值四点(0/0.1/0.5/1)单调——素材实际引用的是这四点的 58.11→55.60 /
#       0.708→0.635 / 2.33→2.12。两种口径分开断言；混读（三点均值 vs 单种子）不是素材主张，
#       见下方 print 的说明。
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
for series, label in ((tau_m, 'τ(三种子均值)'), (top_m, 'zero-shot top-1(三种子均值)'),
                      (val_m, 'val_loss(三种子均值)')):
    if any(series.get(lr) is None for lr in SEEDS3):
        fails.append('B9 均值 %s 缺数据' % label)
        continue
    check('B9 均值 %s 四个三种子点严格递减' % label,
          1.0 if all(series[b] < series[a] for a, b in zip(SEEDS3, SEEDS3[1:])) else 0.0, 1.0, 0)


def seq(series):
    return ' > '.join('%.4f' % series[lr] if series.get(lr) is not None else 'NA' for lr in SWEEP)


print('  seed42  τ    ' + seq(tau42))
print('  seed42  top1 ' + seq(top42))
print('  seed42  val  ' + seq(val42))
print('  均值(4点) τ    ' + ' > '.join('%.4f' % tau_m[lr] for lr in SEEDS3))
print('  均值(4点) top1 ' + ' > '.join('%.4f' % top_m[lr] for lr in SEEDS3))
print('  均值(4点) val  ' + ' > '.join('%.4f' % val_m[lr] for lr in SEEDS3))
print('  注：把三种子均值与单种子中间点混成一条序列读 val（%s）会在 λ=0→0.05 处出现'
      % seq(val_m))
print('      2.3284<2.3376 的“反转”，这是统计口径混合（3 种子均值 vs 单种子），素材并未这样读；')
print('      六点单调性由 seed42 序列承担，均值单调性只在四个三种子点上断言。')

# B9.5 派生百分比：ep1→ep10 的 τ 侵蚀 -6.3%、zero-shot top-1 侵蚀 -2.9%
e1 = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch1.json'))
if e1 is None:
    fails.append('B9 lr0.0/seed42/eval_epoch1.json 缺文件（派生百分比）')
else:
    tau1, tau10 = fnum(e1.get('tau_final')), (fnum(e10.get('tau_final')) if e10 else None)
    p1, p10 = fnum(e1.get('top1_50k')), (fnum(e10.get('top1_50k')) if e10 else None)
    if None in (tau1, tau10, p1, p10):
        fails.append('B9 ep1/ep10 缺 τ/top1 字段（派生百分比）')
    else:
        rel_tau = (tau10 - tau1) / tau1 * 100.0
        rel_top = (p10 - p1) / p1 * 100.0
        check('B9 τ ep1→ep10 相对变化 %', rel_tau, -6.3, 0.05)
        check('B9 top-1 ep1→ep10 相对变化 %', rel_top, -2.9, 0.05)
        check('B9 |τ 侵蚀| > |top-1 侵蚀|', 1.0 if abs(rel_tau) > abs(rel_top) else 0.0, 1.0, 0)
        print('  ep1→ep10 τ %.7f→%.7f = %.4f%%；top-1 %.3f→%.3f = %.4f%%'
              % (tau1, tau10, rel_tau, p1, p10, rel_top))

# B9.6 val_loss 最小值位置：argmin = epoch 3，且 epoch 10 为五点最大
vals_ep = {}
for e in (1, 2, 3, 5, 10):
    d = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'eval_epoch%d.json' % e))
    v = fnum((d or {}).get('val_loss'))
    if v is None:
        fails.append('B9 lr0.0/seed42/eval_epoch%d.json 缺 val_loss' % e)
        continue
    vals_ep[e] = v
if len(vals_ep) == 5:
    check('B9 val_loss argmin = epoch 3', float(min(vals_ep, key=vals_ep.get)), 3.0, 0)
    check('B9 val_loss 最大 = epoch 10', float(max(vals_ep, key=vals_ep.get)), 10.0, 0)
    alt = dict(vals_ep)
    v_r0 = fnum((r0 or {}).get('val_loss'))
    if v_r0 is not None:
        alt[10] = v_r0
        check('B9 改用训练期 ep10 值后 argmin 仍 = epoch 3',
              float(min(alt, key=alt.get)), 3.0, 0)
        check('B9 改用训练期 ep10 值后最大仍 = epoch 10',
              float(max(alt, key=alt.get)), 10.0, 0)
    print('  逐 epoch val_loss ' + ', '.join('ep%d %.6f' % (e, v) for e, v in sorted(vals_ep.items())))

# B9.7 逐样本 τ spread：素材区间 0.26–0.28（复评后；旧稿 0.32 不成立）
sds = {}
for e in (1, 2, 3, 5, 10):
    d = jfile(os.path.join(CLS, 'lr0.0', 'seed42', 'tau_recomputed_ep%d.json' % e))
    v = fnum((d or {}).get('tau_sd_across_samples'))
    if v is None:
        fails.append('B9 lr0.0/seed42/tau_recomputed_ep%d.json 缺 tau_sd_across_samples' % e)
        continue
    sds[e] = v
if sds:
    sd_lo, sd_hi = min(sds.values()), max(sds.values())
    check('B9 逐样本 τ sd 下界(ep1)', sd_lo, 0.2557, 0.0006)
    check('B9 逐样本 τ sd 上界(ep10)', sd_hi, 0.2822, 0.0006)
    check('B9 素材 sd 区间 = 0.26–0.28', 1.0 if (round(sd_lo, 2) == 0.26 and round(sd_hi, 2) == 0.28) else 0.0, 1.0, 0)
    print('  逐 epoch sd ' + ', '.join('ep%d %.6f' % (e, v) for e, v in sorted(sds.items())))

# B9.8 τ 复算溯源：全部来自缓存参考的 5000 张子采样
tr_files = sorted(glob.glob(os.path.join(CLS, 'lr*', 'seed*', 'tau_recomputed_ep*.json')))
src_bad = 0
for p in tr_files:
    d = jfile(p) or {}
    if d.get('sub_indices_source') != 'cache' or fnum(d.get('n_samples')) != 5000.0:
        src_bad += 1
check('B9 τ 复算文件覆盖数 ≥ 14', 1.0 if len(tr_files) >= 14 else 0.0, 1.0, 0)
check('B9 τ 复算文件溯源异常数(sub_indices_source/n_samples)', float(src_bad), 0.0, 0)
print('  τ 复算文件 %d 个：sub_indices_source=cache、n_samples=5000，异常 %d 个'
      % (len(tr_files), src_bad))

print()
print(f'通过 {len(oks)} 项，失败 {len(fails)} 项')
for f in fails:
    print('  FAIL', f)
sys.exit(0 if not fails else 1)

"""重算 tab:dynamics 的 mean±sd（种群标准差口径），并核对 50ep 行。"""
import json
import math
import statistics

dm = json.load(open('outputs/dynamics_matrix.json', encoding='utf-8'))
ds = json.load(open('outputs/dynamics_seed.json', encoding='utf-8'))
print('dynamics_matrix 键:', list(dm.keys()))
print('dynamics_seed 键:', list(ds.keys()))
print()


def series(d, key):
    v = d.get(key)
    return v if isinstance(v, list) else None


def cell(vals):
    if not vals:
        return 'n/a'
    m = sum(vals) / len(vals)
    pop = math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))
    samp = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return 'n=%d 值=%s 均值=%.4f 种群sd=%.4f 样本sd=%.4f' % (len(vals), [round(x, 4) for x in vals], m, pop, samp)


# CLIP+Sonar：dynamics_matrix.clip_sonar（seed42）+ dynamics_seed.clip_sonar_s0/s1
for ep, label in ((0, '@1'), (9, '@10')):
    print('--- CLIP+Sonar %s ---' % label)
    for field in ('tau', 'sigma_m', 'top1'):
        vals = []
        s = series(dm, 'clip_sonar')
        if s and field in s[ep]:
            vals.append(s[ep][field])
        for k in ('clip_sonar_s0', 'clip_sonar_s1'):
            s2 = series(ds, k)
            if s2 and field in s2[ep]:
                vals.append(s2[ep][field])
        print('   %-8s %s' % (field, cell(vals)))

print()
print('--- BioCLIP+Marine 可得的 seed 轨迹 ---')
for k in ds:
    if 'bio_marine' in k:
        s = series(ds, k)
        if s:
            print('   %-16s ep10: tau=%s sigma_m=%s' % (k, s[9].get('tau'), s[9].get('sigma_m')))
for k in dm:
    if 'bio' in k.lower() and 'marine' in k.lower():
        s = series(dm, k)
        if s:
            print('   [matrix] %-12s ep10: tau=%s sigma_m=%s' % (k, s[9].get('tau'), s[9].get('sigma_m')))

print()
print('--- 50ep 行：epoch 1 / 10 / 50 的值 ---')
s = series(ds, 'clip_sonar_50ep')
if s:
    for ep in (0, 9, 49):
        print('   ep%-3d tau=%.4f sigma_m=%.4f top1=%s'
              % (ep + 1, s[ep]['tau'], s[ep]['sigma_m'], s[ep].get('top1')))

"""tab:dynamics 全种子重算（补上 s99 与 ocean_tautraj 的 seed42），统一用种群标准差。"""
import json
import math

dm = json.load(open('outputs/dynamics_matrix.json', encoding='utf-8'))
ds = json.load(open('outputs/dynamics_seed.json', encoding='utf-8'))
ot = json.load(open('outputs/ocean_tautraj.json', encoding='utf-8'))
print('ocean_tautraj 键:', list(ot.keys()))


def get_variants(obj, keys):
    out = {}
    for k in keys:
        v = obj.get(k)
        if isinstance(v, list) and len(v) >= 10:
            out[k] = v
    return out


groups = {
    'BioCLIP+Marine': [('dynamics_seed', ds, ['bio_marine_s0', 'bio_marine_s1']),
                       ('ocean_tautraj', ot, ['marine'])],
    'CLIP+Sonar': [('dynamics_matrix', dm, ['clip_sonar']),
                   ('dynamics_seed', ds, ['clip_sonar_s0', 'clip_sonar_s1', 'clip_sonar_s99'])],
}


def pop(v):
    m = sum(v) / len(v)
    return m, math.sqrt(sum((x - m) ** 2 for x in v) / len(v))


for name, sources in groups.items():
    print()
    print('===== %s =====' % name)
    for ep, lab in ((0, '@1'), (9, '@10')):
        for field in ('tau', 'sigma_m', 'top1'):
            vals, srcs = [], []
            for sname, obj, keys in sources:
                for k in keys:
                    v = obj.get(k)
                    if isinstance(v, list) and len(v) > ep and field in v[ep]:
                        vals.append(float(v[ep][field]))
                        srcs.append('%s.%s' % (sname, k))
            if not vals:
                print('   %-8s %-6s 无数据' % (field, lab))
                continue
            m, sd = pop(vals)
            print('   %-8s %-6s n=%d 均值=%.4f 种群sd=%.4f | %s'
                  % (field, lab, len(vals), m, sd, [round(x, 4) for x in vals]))

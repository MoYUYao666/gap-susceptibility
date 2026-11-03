"""A2 扩展 Part V 素材: 类构成机制汇总 —— 从已有 JSON 重建 σ_m 与 (类数/来源/margin 结构) 关系表。
输出: outputs/mechanism_summary.json (纯重析, 零 GPU)
运行: python tools/clip_mechanism_summary.py
"""
import json, os, collections

OUT = 'outputs/mechanism_summary.json'


def load(p):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def main():
    res = {'sources': {}}
    # 1) 类目数扫描 (海洋)
    ns = load('outputs/ocean_nsweep.json') or {}
    nsT = []
    for tag in ['bioclip', 'oceanclip']:
        for N, v in sorted(ns.get(tag, {}).items(), key=lambda kv: int(kv[0])):
            nsT.append({'model': tag, 'N': int(N), 'n_images': v['n_images'],
                        'sigma_m': v['sigma_m'], 'top1_0': v['top1_0'], 'top1_1': v['top1_1'],
                        'retention1': v['top1_1'] / v['top1_0'] if v['top1_0'] else None,
                        'tau1': v['tau_meas_1']})
    res['sources']['nsweep'] = {'rows': nsT}
    # 2) 类集构成 (fish-67 / fauna-117 / inat-48) σ_m + 保留
    ma = load('outputs/ocean_margins.json') or {}
    fa = load('outputs/ocean_fauna_margins.json') or {}
    iw = load('outputs/ocean_inat_wild.json') or {}
    comp = []
    for name, data, keys in [('fish-67', ma, ['bioclip', 'oceanclip']),
                             ('fauna-117', fa, ['bioclip', 'oceanclip']),
                             ('inat-48', iw, ['bioclip', 'oceanclip'])]:
        for k in keys:
            if k in data:
                d = data[k]
                meas = d.get('measured', {})
                top1_0 = meas.get('0.0', {}).get('top1', None)
                top1_1 = meas.get('1.0', {}).get('top1', None)
                comp.append({'set': name, 'model': k, 'sigma_m': d.get('sigma_m'),
                             'mean_m': d.get('mean_m'),
                             'top1_0': top1_0, 'top1_1': top1_1,
                             'tau1': (meas.get('1.0') or {}).get('tau'),
                             'retention1': (top1_1 / top1_0) if (top1_0 and top1_1) else None})
    res['sources']['class_set'] = comp
    # 3) 2x2 判别 (域 vs 剂量) —— 从 ocean_clip2x2 / margins 表重建
    c2 = load('outputs/ocean_clip2x2.json') or {}
    res['sources']['dose2x2'] = c2.get('summary', c2)
    # 4) 声呐双口径
    sp = load('outputs/sonar_protocol_full.json') or {}
    son = []
    for k, v in sp.items():
        if k == 'meta':
            continue
        r1 = next((r for r in v.get('rows', []) if r.get('lambda') == 1.0), {})
        son.append({'model': k, 'sigma_m': v.get('sigma_m'), 'top1_0': v.get('top1_0'),
                    'tau1': r1.get('tau_meas'), 'n': sp['meta'].get('n_images')})
    res['sources']['sonar'] = son
    # 5) 域矩阵 (若已存在)
    dm = load('outputs/domain_matrix.json') or {}
    if dm:
        dmrows = []
        for dom, models in dm.items():
            if dom == 'meta':
                continue
            for mid, v in models.items():
                if not isinstance(v, dict) or 'rows' not in v:
                    continue
                r1 = next((r for r in v.get('rows', []) if r.get('lambda') == 1.0), {})
                dmrows.append({'domain': dom, 'model': mid, 'sigma_m': v.get('sigma_m'),
                               'top1_0': v.get('top1_0'), 'tau1': r1.get('tau_meas'),
                               'tau_pred1': r1.get('tau_pred'), 'ncc_0': v.get('ncc_0')})
        res['sources']['domain_matrix'] = dmrows
    # 6) 任务谱系 (海洋 + 声呐)
    res['sources']['spectrum_marine'] = load('outputs/ocean_spectrum.json')
    res['sources']['spectrum_sonar'] = load('outputs/sonar_spectrum.json')
    # 7) PEFT 汇总
    res['sources']['peft_marine'] = load('outputs/ocean_peft_ms.json')
    res['sources']['peft_sonar'] = load('outputs/sonar_peft_ms.json')
    # 8) 方向算子/退化
    res['sources']['degradation_marine'] = load('outputs/ocean_degradation.json')
    res['sources']['degradation_sonar'] = load('outputs/sonar_degradation.json')
    res['sources']['direction_operator'] = load('outputs/direction_operator.json')
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('rows: nsweep=%d class_set=%d sonar=%d domain=%d' %
          (len(nsT), len(comp), len(son), len(res['sources'].get('domain_matrix', []))))
    print('DONE ->', OUT)


if __name__ == '__main__':
    main()

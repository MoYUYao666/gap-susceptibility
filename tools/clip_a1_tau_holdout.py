"""(A1 备战) τ 的独立性与泛化验证 + 关键数字溯源计算。

任务:
  1) 理论预测 vs 实测 τ: 从 outputs/a1_margins.json 逐 λ 对比 predicted_tau_{exact,gauss}
     与 measured_tau_5k / measured_tau_50k —— 独立复算相关性与误差(不采信已有的 r=1.0 结论)。
  2) 跨模型泛化(留一模型): 用 a1_full_results + a1_crossmodel_results(+其它含 τ/top1 的结果),
     对比"top1 ~ τ"与"top1 ~ CG"两种预测子在留出模型上的表现, 回答"τ 是否只是描述性/同义反复"。
  3) 条件计数与关键数字: 核对摘要里的 34 条件 / CG 0.82→0.01 / top1 59.3%→32.0% / +0.114 等
     的出处(逐文件统计 + 极值定位)。
输出: outputs/a1_tau_holdout.json
"""
import glob
import json
import os

import numpy as np
from scipy import stats

OUT = 'outputs/a1_tau_holdout.json'


def load(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def rows_from(fn):
    """把含 model/lambda/CG/tau_top5/top1 的记录统一成行。"""
    d = load(fn)
    out = []
    if isinstance(d, list):
        for r in d:
            if all(k in r for k in ('CG', 'top1', 'tau_top5')):
                out.append({'file': os.path.basename(fn), 'model': r.get('model', '?'),
                            'kind': r.get('kind', ''), 'lam': r.get('lambda'),
                            'CG': float(r['CG']), 'tau': float(r['tau_top5']), 'top1': float(r['top1'])})
    elif isinstance(d, dict) and isinstance(d.get('results'), list):
        for r in d['results']:
            if all(k in r for k in ('CG', 'top1', 'tau_top5')):
                out.append({'file': os.path.basename(fn), 'model': d.get('model', '?'),
                            'kind': r.get('kind', ''), 'lam': r.get('lambda'),
                            'CG': float(r['CG']), 'tau': float(r['tau_top5']), 'top1': float(r['top1'])})
    return out


def fit_predict(tr, te, xkey):
    x = np.array([r[xkey] for r in tr], dtype=float)
    y = np.array([r['top1'] for r in tr], dtype=float)
    b, a = np.polyfit(x, y, 1)
    xt = np.array([r[xkey] for r in te], dtype=float)
    yt = np.array([r['top1'] for r in te], dtype=float)
    pred = a + b * xt
    ss_res = float(((yt - pred) ** 2).sum())
    ss_tot = float(((yt - yt.mean()) ** 2).sum())
    return {'slope': round(float(b), 3), 'intercept': round(float(a), 3),
            'r2_holdout': round(1 - ss_res / ss_tot, 4) if ss_tot > 0 else None,
            'mae_holdout': round(float(np.abs(yt - pred).mean()), 3), 'n_holdout': len(te)}


def main():
    files = ['outputs/a1_full_results.json', 'outputs/a1_crossmodel_results.json',
             'outputs/a1_text_surgery.json', 'outputs/a1_dinov2_surgery.json',
             'outputs/a1_qwen_surgery_v3.json', 'outputs/a1_multitemplate.json',
             'outputs/a1_subspace_results.json', 'outputs/a1_e2b_e3b.json']
    rows = []
    for f in files:
        rows += rows_from(f)

    # ---- 1) 理论预测 vs 实测 τ ----
    mg = load('outputs/a1_margins.json') or {}
    theory = {}
    for pk, mk in (('predicted_tau_exact', 'measured_tau_5k'), ('predicted_tau_gauss', 'measured_tau_5k'),
                   ('predicted_tau_exact', 'measured_tau_50k'), ('predicted_tau_gauss', 'measured_tau_50k')):
        p, m = mg.get(pk), mg.get(mk)
        if not p or not m:
            continue
        keys = [k for k in p if k in m]
        pv = np.array([p[k] for k in keys], dtype=float)
        mv = np.array([(m[k]['tau'] if isinstance(m[k], dict) else m[k]) for k in keys], dtype=float)
        pr = stats.pearsonr(pv, mv)
        sp = stats.spearmanr(pv, mv)
        theory['%s_vs_%s' % (pk, mk)] = {
            'n': len(keys), 'pearson_r': round(float(pr[0]), 5), 'pearson_p': float(pr[1]),
            'spearman_r': round(float(sp[0]), 5),
            'max_abs_diff': round(float(np.abs(pv - mv).max()), 4),
            'mean_abs_diff': round(float(np.abs(pv - mv).mean()), 4),
            'identical': bool(np.allclose(pv, mv, atol=1e-12)),
            'predicted': {k: round(float(p[k]), 4) for k in keys},
            'measured': {k: round(float((m[k]['tau'] if isinstance(m[k], dict) else m[k])), 4) for k in keys}}

    # ---- 2) 跨模型泛化(留一模型) ----
    models = sorted({r['model'] for r in rows})
    pooled = {}
    if len(rows) > 3:
        tau = np.array([r['tau'] for r in rows]); cg = np.array([r['CG'] for r in rows])
        top = np.array([r['top1'] for r in rows])
        for nm, x in (('tau', tau), ('CG', cg)):
            pr = stats.pearsonr(x, top); sp = stats.spearmanr(x, top)
            pooled[nm] = {'pearson_r': round(float(pr[0]), 4), 'pearson_p': float(pr[1]),
                          'spearman_r': round(float(sp[0]), 4), 'spearman_p': float(sp[1])}
    lomo = {}
    for m in models:
        tr = [r for r in rows if r['model'] != m]
        te = [r for r in rows if r['model'] == m]
        if len(tr) > 2 and len(te) >= 1 and len({r['tau'] for r in tr}) > 1:
            lomo[m] = {'n_train': len(tr), 'n_test': len(te),
                       'tau_predictor': fit_predict(tr, te, 'tau'),
                       'CG_predictor': fit_predict(tr, te, 'CG')}

    # ---- 3) 条件计数与关键数字 ----
    per_file = {}
    for f in files:
        rs = rows_from(f)
        if rs:
            per_file[os.path.basename(f)] = {'n_conditions': len(rs), 'models': sorted({r['model'] for r in rs})}
    cg_vals = [r['CG'] for r in rows]
    top_vals = [r['top1'] for r in rows]
    tau_vals = [r['tau'] for r in rows]
    key = {'total_conditions_with_metrics': len(rows),
           'CG_min': round(min(cg_vals), 4) if cg_vals else None,
           'CG_max': round(max(cg_vals), 4) if cg_vals else None,
           'top1_min': round(min(top_vals), 3) if top_vals else None,
           'top1_max': round(max(top_vals), 3) if top_vals else None,
           'tau_min': round(min(tau_vals), 4) if tau_vals else None,
           'tau_max': round(max(tau_vals), 4) if tau_vals else None}
    bm = load('outputs/a1_baseline_metrics.json') or {}
    key['baseline_metrics_n_conditions'] = bm.get('n_conditions')
    key['baseline_metric_correlations'] = bm.get('metric_correlations')
    key['baseline_theory_verification'] = bm.get('theory_verification')

    res = {'theory_vs_measured_tau': theory, 'pooled_predictors': pooled, 'leave_one_model_out': lomo,
           'conditions_per_file': per_file, 'key_numbers': key,
           'rows_summary': {'n_rows': len(rows), 'models': models}}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    print('rows with (CG,tau,top1):', len(rows), '| models:', models)
    print('pooled:', json.dumps(pooled))
    for m, v in lomo.items():
        print('LOMO %-9s tau R2=%-8s MAE=%-7s | CG R2=%-8s MAE=%s' % (
            m, v['tau_predictor']['r2_holdout'], v['tau_predictor']['mae_holdout'],
            v['CG_predictor']['r2_holdout'], v['CG_predictor']['mae_holdout']))
    for k, v in theory.items():
        print('theory %-42s n=%d r=%.4f maxdiff=%.4f identical=%s' % (k, v['n'], v['pearson_r'],
                                                                      v['max_abs_diff'], v['identical']))
    print('conditions per file:', json.dumps({k: v['n_conditions'] for k, v in per_file.items()}))
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()

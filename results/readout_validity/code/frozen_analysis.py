"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr
import statistics as st


def spearman(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return {'rho': None, 'p': None, 'n': int(m.sum())}
    r = spearmanr(a[m], b[m])
    return {'rho': float(r.correlation), 'p': float(r.pvalue), 'n': int(m.sum())}

def get(row, cond, key):
    v = row.get(cond, {}).get(key)
    return float(v) if isinstance(v, (int, float)) else None

def analyze(d):
    rows = []
    for key, v in d.items():
        enc, ds = key.split('__')
        rows.append({'cell': key, 'encoder': enc, 'dataset': ds, 'kind': v['kind']})
    for cond in ('original', 'mean_center', 'gap_project', 'random_project'):
        for r in rows:
            src = d[r['cell']][cond]
            for k in ('CG', 'DG', 'spec_eff_rank', 'spec_top1_share'):
                r[cond + '_' + k] = src['gap'][k]
    readout_keys = ['classification_top1', 'R1_i2t', 'R1_t2i', 'R5_i2t', 'ARI', 'mixed_R1']
    for cond in ('original', 'mean_center', 'gap_project', 'random_project'):
        for r in rows:
            src = d[r['cell']][cond]
            for k in readout_keys:
                r[cond + '_' + k] = src.get(k)
    out = {'n_cells': len(rows), 'cells': rows}
    cg = [r['original_CG'] for r in rows]
    dg = [r['original_DG'] for r in rows]
    out['C1_original_CG_DG_spearman'] = spearman(cg, dg)
    out['C1_original_CG_DG_pearson'] = {'r': float(np.corrcoef(cg, dg)[0, 1]), 'n': len(rows)}
    for cond in ('mean_center', 'gap_project', 'random_project'):
        out['C1_%s_CG_DG_spearman' % cond] = spearman([r[cond + '_CG'] for r in rows], [r[cond + '_DG'] for r in rows])
    out['C1_cg_dg_ratio_by_condition'] = {}
    for cond in ('original', 'mean_center', 'gap_project', 'random_project'):
        c = np.asarray([r[cond + '_CG'] for r in rows])
        g = np.asarray([r[cond + '_DG'] for r in rows])
        out['C1_cg_dg_ratio_by_condition'][cond] = {'CG_mean': float(c.mean()), 'DG_mean': float(g.mean()), 'CG_over_DG': float(c.mean() / max(g.mean(), 1e-12))}
    out['C2_effect_means'] = {}
    for cond in ('mean_center', 'gap_project', 'random_project'):
        eff = {}
        for k in readout_keys:
            vals = [r[cond + '_' + k] - r['original_' + k] for r in rows if r[cond + '_' + k] is not None and r['original_' + k] is not None]
            if vals:
                eff[k] = {'mean': float(st.mean(vals)), 'sd': float(st.stdev(vals)) if len(vals) > 1 else 0.0, 'n': len(vals)}
        out['C2_effect_means'][cond] = eff
    out['C2_direction_counts'] = {}
    for kind in ('class', 'caption'):
        for cond in ('mean_center', 'gap_project', 'random_project'):
            sub = [r for r in rows if r['kind'] == kind]
            cnt = {}
            for k in readout_keys:
                vals = [r[cond + '_' + k] - r['original_' + k] for r in sub if r[cond + '_' + k] is not None and r['original_' + k] is not None]
                if vals:
                    cnt[k] = {'n': len(vals), 'improved': int(sum((v > 0 for v in vals))), 'worse': int(sum((v < 0 for v in vals)))}
            out['C2_direction_counts']['%s__%s' % (kind, cond)] = cnt
    out['C3_predictive_spearman'] = {}
    for kind in ('class', 'caption'):
        sub = [r for r in rows if r['kind'] == kind]
        for metric in ('CG', 'DG', 'spec_eff_rank', 'spec_top1_share'):
            for target in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
                a = [r['original_' + metric] for r in sub]
                b = [r['original_' + target] for r in sub]
                out['C3_predictive_spearman']['%s__%s__%s' % (kind, metric, target)] = spearman(a, b)
    out['C4_readout_rank_agreement'] = {}
    for kind in ('class', 'caption'):
        sub = [r for r in rows if r['kind'] == kind]
        pairs = [('classification_top1', 'R1_i2t'), ('classification_top1', 'R1_t2i'), ('R1_i2t', 'R1_t2i'), ('R1_i2t', 'ARI'), ('R1_t2i', 'ARI')]
        for a, b in pairs:
            if a == 'classification_top1' and kind != 'class':
                continue
            out['C4_readout_rank_agreement']['%s__%s__%s' % (kind, a, b)] = spearman([r['original_' + a] for r in sub if r['original_' + a] is not None and r['original_' + b] is not None], [r['original_' + b] for r in sub if r['original_' + a] is not None and r['original_' + b] is not None])
    return out

"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr
import statistics as st


def sp(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return {'rho': None, 'p': None, 'n': int(m.sum())}
    r = spearmanr(a[m], b[m])
    return {'rho': float(r.correlation), 'p': float(r.pvalue), 'n': int(m.sum())}

def fit_cv(rows, xkey, ykey, group):
    xs = np.asarray([r[xkey] for r in rows], float)
    ys = np.asarray([r[ykey] for r in rows], float)
    groups = np.asarray([r[group] for r in rows])
    pred = np.full(len(xs), np.nan)
    for g in sorted(set(groups.tolist())):
        te = groups == g
        tr = ~te
        if tr.sum() < 3 or te.sum() == 0:
            continue
        A = np.column_stack([np.ones(tr.sum()), xs[tr]])
        beta, *_ = np.linalg.lstsq(A, ys[tr], rcond=None)
        pred[te] = beta[0] + beta[1] * xs[te]
    ok = np.isfinite(pred)
    if ok.sum() < 3:
        return None
    r = pearsonr(pred[ok], ys[ok])[0]
    ss_res = ((ys[ok] - pred[ok]) ** 2).sum()
    ss_tot = ((ys[ok] - ys[ok].mean()) ** 2).sum()
    return {'pearson': float(r), 'r2': float(1 - ss_res / ss_tot) if ss_tot else None, 'spearman': float(spearmanr(pred[ok], ys[ok]).correlation), 'n': int(ok.sum())}

def analyze(d):
    rows = []
    for run in d['runs']:
        meta = run['run']
        for e in run['epochs']:
            for cond, m in e['conditions'].items():
                r = {'backbone': meta['backbone'], 'dataset': meta['dataset'], 'rank': meta['rank'], 'seed': meta['seed'], 'tower': meta.get('tower', 'both'), 'epoch': e['epoch'], 'condition': cond, 'train_loss': e['train_loss']}
                for k, v in m.items():
                    r[k] = v
                rows.append(r)
    orig = [r for r in rows if r['condition'] == 'original']
    out = {'n_runs': len(d['runs']), 'n_checkpoints': len(orig), 'n_rows': len(rows)}
    out['CG_DG'] = {}
    for cond in ('original', 'mean_center', 'gap_project', 'random_project'):
        sub = [r for r in rows if r['condition'] == cond]
        out['CG_DG'][cond] = sp([r['CG'] for r in sub], [r['DG'] for r in sub])
        out['CG_DG'][cond]['CG_mean'] = float(np.mean([r['CG'] for r in sub]))
        out['CG_DG'][cond]['DG_mean'] = float(np.mean([r['DG'] for r in sub]))
    out['interventions'] = {}
    out['by_tower_interventions'] = {}
    for tw in sorted(set((r['tower'] for r in orig))):
        tw_eff = {}
        for cond in ('mean_center', 'gap_project', 'random_project'):
            eff = {}
            for k in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
                vals = []
                for r in orig:
                    if r['tower'] != tw:
                        continue
                    other = next((x for x in rows if x['condition'] == cond and x['backbone'] == r['backbone'] and (x['dataset'] == r['dataset']) and (x['rank'] == r['rank']) and (x['seed'] == r['seed']) and (x['epoch'] == r['epoch']) and (x['tower'] == r['tower'])), None)
                    if other and np.isfinite(r[k]) and np.isfinite(other[k]):
                        vals.append(other[k] - r[k])
                if vals:
                    eff[k] = {'mean': float(np.mean(vals)), 'sd': float(np.std(vals)), 'n': len(vals)}
            tw_eff[cond] = eff
        out['by_tower_interventions'][tw] = tw_eff
    for cond in ('mean_center', 'gap_project', 'random_project'):
        eff = {}
        for k in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
            vals = []
            for r in orig:
                other = next((x for x in rows if x['condition'] == cond and x['backbone'] == r['backbone'] and (x['dataset'] == r['dataset']) and (x['rank'] == r['rank']) and (x['seed'] == r['seed']) and (x['epoch'] == r['epoch']) and (x['tower'] == r['tower'])), None)
                if other and np.isfinite(r[k]) and np.isfinite(other[k]):
                    vals.append(other[k] - r[k])
            if vals:
                eff[k] = {'mean': float(np.mean(vals)), 'sd': float(np.std(vals)), 'n': len(vals), 'improved': int(sum((v > 0 for v in vals))), 'worse': int(sum((v < 0 for v in vals)))}
        out['interventions'][cond] = eff
    out['predictive'] = {}
    for m in ('CG', 'DG', 'spec_eff_rank', 'spec_top1_share'):
        for target in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
            out['predictive']['%s__%s' % (m, target)] = sp([r[m] for r in orig], [r[target] for r in orig])
    out['by_tower_predictive'] = {}
    for tw in sorted(set((r['tower'] for r in orig))):
        sub = [r for r in orig if r['tower'] == tw]
        out['by_tower_predictive'][tw] = {}
        for m in ('CG', 'DG', 'spec_eff_rank', 'spec_top1_share'):
            for target in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
                out['by_tower_predictive'][tw]['%s__%s' % (m, target)] = sp([r[m] for r in sub], [r[target] for r in sub])
    out['grouped'] = {}
    for m in ('CG', 'DG', 'spec_eff_rank', 'spec_top1_share'):
        for target in ('classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
            for g in ('dataset', 'backbone', 'tower'):
                out['grouped']['%s__%s__%s' % (m, target, g)] = fit_cv(orig, m, target, g)
    deltas = []
    for run in d['runs']:
        es = sorted(run['epochs'], key=lambda x: x['epoch'])
        if len(es) < 2:
            continue
        a, b = (es[0]['conditions']['original'], es[-1]['conditions']['original'])
        row = {'backbone': run['run']['backbone'], 'dataset': run['run']['dataset'], 'rank': run['run']['rank'], 'seed': run['run']['seed'], 'tower': run['run'].get('tower', 'both')}
        for k in ('CG', 'DG', 'spec_eff_rank', 'classification_top1', 'R1_i2t', 'R1_t2i', 'ARI'):
            row['d' + k] = b[k] - a[k]
        deltas.append(row)
    out['delta_predictive'] = {}
    for m in ('dCG', 'dDG', 'dspec_eff_rank'):
        for target in ('dclassification_top1', 'dR1_i2t', 'dR1_t2i', 'dARI'):
            out['delta_predictive']['%s__%s' % (m, target)] = sp([r[m] for r in deltas], [r[target] for r in deltas])
    out['n_delta_runs'] = len(deltas)
    out['by_tower'] = {}
    for tw in sorted(set((r['tower'] for r in orig))):
        sub = [r for r in orig if r['tower'] == tw]
        out['by_tower'][tw] = {'n_checkpoints': len(sub), 'CG': float(np.mean([r['CG'] for r in sub])), 'DG': float(np.mean([r['DG'] for r in sub])), 'spec_eff_rank': float(np.mean([r['spec_eff_rank'] for r in sub])), 'classification_top1': float(np.mean([r['classification_top1'] for r in sub])), 'R1_i2t': float(np.mean([r['R1_i2t'] for r in sub])), 'R1_t2i': float(np.mean([r['R1_t2i'] for r in sub])), 'ARI': float(np.mean([r['ARI'] for r in sub]))}
    out['by_dataset'] = {}
    for ds in sorted(set((r['dataset'] for r in orig))):
        sub = [r for r in orig if r['dataset'] == ds]
        out['by_dataset'][ds] = {'n_checkpoints': len(sub), 'CG': float(np.mean([r['CG'] for r in sub])), 'DG': float(np.mean([r['DG'] for r in sub])), 'spec_eff_rank': float(np.mean([r['spec_eff_rank'] for r in sub])), 'classification_top1': float(np.mean([r['classification_top1'] for r in sub])), 'R1_i2t': float(np.mean([r['R1_i2t'] for r in sub])), 'R1_t2i': float(np.mean([r['R1_t2i'] for r in sub])), 'ARI': float(np.mean([r['ARI'] for r in sub]))}
    return out

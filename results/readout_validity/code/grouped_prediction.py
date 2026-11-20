"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr
import statistics as st


def fit_predict(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A_ = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(A_, y, rcond=None)
    return (A_ @ beta, beta)

def cv(rows, metric, target, group):
    xs = [r['original_' + metric] for r in rows]
    ys = [r['original_' + target] for r in rows]
    groups = [r[group] for r in rows]
    pred = np.full(len(xs), np.nan)
    for g in sorted(set(groups)):
        te = np.array([gg == g for gg in groups])
        tr = ~te
        if tr.sum() < 3 or te.sum() == 0:
            continue
        _, beta = fit_predict(np.asarray(xs)[tr], np.asarray(ys)[tr])
        xte = np.asarray(xs)[te]
        pred[te] = beta[0] + beta[1] * xte
    ok = np.isfinite(pred)
    if ok.sum() < 3:
        return None
    rr = pearsonr(pred[ok], np.asarray(ys)[ok])[0]
    ss_res = ((np.asarray(ys)[ok] - pred[ok]) ** 2).sum()
    ss_tot = ((np.asarray(ys)[ok] - np.asarray(ys)[ok].mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot else None
    return {'pearson': float(rr), 'r2': float(r2) if r2 is not None else None, 'spearman': float(spearmanr(pred[ok], np.asarray(ys)[ok]).correlation), 'n': int(ok.sum())}

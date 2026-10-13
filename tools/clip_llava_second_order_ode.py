"""Tier A8: model the rebound trajectory of the decoder alignment energy with a second-order (damped oscillation) model.

Background (second half of limitation 16 in the paper): the first-order ODE dE/dt = -α(E-E*) of §3b was only fitted on monotonic two-tower trajectories;
the decoder trajectory is non-monotonic (first falls, then rises) and needs a second-order / overshoot term, but that correction had not been modeled before.

This script compares three models on the same batch of 10-epoch trajectories (least squares, scipy curve_fit):
  M0 first order (paper form)      : E(t) = E* + (E0-E*) exp(-a t)                (3 params)
  M1 first order + linear drift     : E(t) = E* + (E0-E*) exp(-a t) + g t          (4 params)
  M2 damped second order (oscillation)     : E(t) = Einf + A exp(-l t) cos(w t + phi)      (5 params)
Report R^2, AICc, the parameters and the damping ratio zeta = l / sqrt(l^2 + w^2) for each rank,
as well as the maximum residual of the first-order model on the rebound segment.
Input: paper3/scripts/outputs/experiments/verify_r{4,5,6,8}_s42_e10.json
Output: outputs/llava_second_order_ode.json
"""
import glob
import json
import os

import numpy as np
from scipy.optimize import curve_fit

OUT = 'outputs/llava_second_order_ode.json'
SRC = 'paper3/scripts/outputs/experiments'
RANKS = [4, 5, 6, 8]


def m0(t, Einf, E0, a):
    return Einf + (E0 - Einf) * np.exp(-a * t)


def m1(t, Einf, E0, a, g):
    return Einf + (E0 - Einf) * np.exp(-a * t) + g * t


def m2(t, Einf, A, l, w, phi):
    return Einf + A * np.exp(-l * t) * np.cos(w * t + phi)


def aicc(rss, n, k):
    if rss <= 0:
        return -np.inf
    aic = n * np.log(rss / n) + 2 * k
    return aic + (2 * k * (k + 1)) / max(n - k - 1, 1)


def r2(y, yhat):
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')


def fit_one(t, y, model, p0, bounds, k):
    popt, _ = curve_fit(model, t, y, p0=p0, bounds=bounds, maxfev=200000)
    yhat = model(t, *popt)
    rss = float(((y - yhat) ** 2).sum())
    return {'params': [round(float(v), 5) for v in popt],
            'r2': round(r2(y, yhat), 4),
            'rmse': round(float(np.sqrt(rss / len(y))), 2),
            'aicc': round(float(aicc(rss, len(y), k)), 2)}


def find_traj(rank):
    """Locate the 10-epoch trajectory of this rank (compatible with both namings: verify_rN_s42_e10.json and the fully tagged version)."""
    pats = [os.path.join(SRC, f'verify_r{rank}_s42_e10.json'),
            os.path.join(SRC, f'verify_r{rank}_s42_*e10*.json')]
    for p in pats:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[0]
    return None


def main():
    traj = {}
    for r in RANKS:
        p = find_traj(r)
        if not p:
            print('missing (will be skipped): rank', r)
            continue
        d = json.load(open(p, encoding='utf-8'))
        E = d['E']
        # keep only the numeric segment (before the NaN)
        vals = []
        for i, v in enumerate(E):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                break
            vals.append(float(v))
        traj[r] = {'epochs': list(range(len(vals))), 'E': vals,
                   'n_nan_tail': len(E) - len(vals), 'note': d.get('note', '')}

    res = {}
    for r, d in traj.items():
        t = np.array(d['epochs'], dtype=float)
        y = np.array(d['E'], dtype=float)
        if len(t) < 5:
            print(f'r{r}: only {len(t)} points, skipped')
            continue
        f0 = fit_one(t, y, m0, p0=[y.min(), y[0], 0.2],
                     bounds=([-1e5, -1e6, 1e-4], [1e6, 1e6, 20.0]), k=3)
        f1 = fit_one(t, y, m1, p0=[y.min(), y[0], 0.3, 100.0],
                     bounds=([-1e5, -1e6, 1e-4, -1e5], [1e6, 1e6, 20.0, 1e5]), k=4)
        f2 = fit_one(t, y, m2, p0=[y.min(), y[0] - y.min(), 0.15, 0.6, 0.0],
                     bounds=([-1e5, -1e6, -5.0, 0.0, -np.pi], [1e6, 1e6, 5.0, 6.28, np.pi]), k=5)
        # damping ratio: zeta = lambda / sqrt(lambda^2 + omega^2)
        Einf, A, l, w, phi = f2['params']
        zeta = l / np.sqrt(l ** 2 + w ** 2) if (l ** 2 + w ** 2) > 0 else float('nan')
        # maximum residual of the first-order model on the rebound segment (points after the observed minimum)
        y0 = m0(t, *f0['params'])
        imin = int(np.argmin(y))
        tail_res = float(np.max(np.abs(y[imin:] - y0[imin:]))) if imin < len(y) - 1 else 0.0
        res[f'r{r}'] = {'n_points': len(t), 'E': d['E'], 'nan_tail': d['n_nan_tail'],
                        'M0_first_order': f0, 'M1_first_order_drift': f1,
                        'M2_damped_second_order': f2,
                        'damping_ratio_zeta': round(float(zeta), 4),
                        'M0_max_abs_residual_after_min': round(tail_res, 2),
                        'model_selection': ('M2' if f2['aicc'] < min(f0['aicc'], f1['aicc'])
                                            else ('M1' if f1['aicc'] < f0['aicc'] else 'M0'))}
    summary = {
        'ranks': list(res.keys()),
        'M0_mean_r2': round(float(np.mean([res[k]['M0_first_order']['r2'] for k in res])), 4) if res else None,
        'M1_mean_r2': round(float(np.mean([res[k]['M1_first_order_drift']['r2'] for k in res])), 4) if res else None,
        'M2_mean_r2': round(float(np.mean([res[k]['M2_damped_second_order']['r2'] for k in res])), 4) if res else None,
        'selected_model_per_rank': {k: res[k]['model_selection'] for k in res},
        'zeta_per_rank': {k: res[k]['damping_ratio_zeta'] for k in res},
        'M0_residual_after_min_per_rank': {k: res[k]['M0_max_abs_residual_after_min'] for k in res},
    }
    json.dump({'trajectories': traj, 'fits': res, 'summary': summary},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(summary, indent=1), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()

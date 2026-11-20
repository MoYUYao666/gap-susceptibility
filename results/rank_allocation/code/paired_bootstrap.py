"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
VQA_MARGIN = 0.05
ALPHA = 0.05


def vqa_contrast(a: dict, b: dict, rng: np.random.Generator, n_boot: int) -> dict:
    """Paired (by question) percentile bootstrap for arm a minus arm b, both metrics."""
    n = a['correct'].size
    idx = rng.integers(0, n, size=(n_boot, n))
    out = {}
    for key, field in (('accuracy', 'correct'), ('token_f1', 'f1')):
        da, db = (a[field], b[field])
        d = da[idx].mean(axis=1) - db[idx].mean(axis=1)
        lo90, hi90 = (float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0)))
        p_lower = float(np.mean(d <= -VQA_MARGIN))
        p_upper = float(np.mean(d >= +VQA_MARGIN))
        out[key] = {'n_boot': int(n_boot), 'delta': float(da.mean() - db.mean()), 'boot_mean': float(d.mean()), 'boot_se': float(d.std(ddof=1)), 'ci95': [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], 'ci90': [lo90, hi90], 'excludes_zero_95': bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0), 'p_one_sided_positive': float(np.mean(d <= 0.0)), 'tost_margin': VQA_MARGIN, 'tost_p_lower': p_lower, 'tost_p_upper': p_upper, 'tost_p': max(p_lower, p_upper), 'equivalent_at_declared_margin': bool(max(p_lower, p_upper) < ALPHA), 'min_equivalent_margin': max(-lo90, hi90)}
    return out

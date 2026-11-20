"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr


def unit(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError('Expected finite two-dimensional vectors')
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norms <= 1e-12):
        raise ValueError('Zero or degenerate vectors cannot be normalized')
    return x / norms

def direction(dimension, seed):
    return unit(np.random.default_rng(seed).normal(size=(1, dimension)))[0]

def targeted(img, txt, mode):
    if mode == 'mean_center':
        return (unit(img - img.mean(0)), unit(txt - txt.mean(0)))
    if mode != 'gap_project':
        raise ValueError(mode)
    d = unit((img.mean(0) - txt.mean(0))[None])[0]
    return (unit(img - np.outer(img @ d, d)), unit(txt - np.outer(txt @ d, d)))

def normmatched(x, target, u):
    """Rotate each row on the sphere by its targeted chord displacement."""
    x, target = (np.asarray(x, float), np.asarray(target, float))
    if x.shape != target.shape or not np.isfinite(target).all():
        raise ValueError('Target must be finite and match input shape')
    if not np.allclose(np.linalg.norm(x, axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError('Input rows must have unit norm')
    if not np.allclose(np.linalg.norm(target, axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError('Target rows must have unit norm')
    u = unit(np.asarray(u)[None])[0]
    tangent = u - (x @ u)[:, None] * x
    lengths = np.linalg.norm(tangent, axis=1)
    if np.any(lengths <= 1e-12):
        raise ValueError('Random direction parallel to a row: undefined tangent')
    tangent /= lengths[:, None]
    cosine = np.clip(np.einsum('ij,ij->i', x, target), -1.0, 1.0)
    radius = np.linalg.norm(target - x, axis=1)
    cosine[radius < 1e-14] = 1.0
    cosine[np.linalg.norm(target + x, axis=1) < 1e-14] = -1.0
    sine = np.sqrt(np.maximum(0.0, 1 - cosine * cosine))
    return cosine[:, None] * x + sine[:, None] * tangent

def readouts(img, txt, labels, kind):
    s = np.einsum('ik,jk->ij', img, txt, optimize=False)
    if kind == 'caption':
        if len(img) != len(txt):
            raise ValueError('Caption protocol requires square aligned features')
        diag = np.diag(s)
        ri = (s > diag[:, None]).sum(1) + 1
        rt = (s > diag[None, :]).sum(0) + 1
        result = {f'R{k}_{side}': float(100 * np.mean(ranks <= k)) for side, ranks in (('i2t', ri), ('t2i', rt)) for k in (1, 5)}
    elif kind == 'class':
        if len(labels) != len(img) or labels.min() < 0 or labels.max() >= len(txt):
            raise ValueError('Class labels do not index the text prototypes')
        diag = s[np.arange(len(img)), labels]
        ri = (s > diag[:, None]).sum(1) + 1
        result = {'classification_top1': float(100 * np.mean(s.argmax(1) == labels)), 'R1_i2t': float(100 * np.mean(ri <= 1)), 'R5_i2t': float(100 * np.mean(ri <= 5)), 'R1_t2i': float(100 * np.mean(labels[s.argmax(0)] == np.arange(len(txt))))}
    else:
        raise ValueError(kind)
    tt = np.einsum('ik,jk->ij', txt, txt, optimize=False)
    np.fill_diagonal(tt, -np.inf)
    pick_img = s.argmax(0)
    cross = s[pick_img, np.arange(len(txt))]
    wins = cross >= tt.max(1)
    correct = pick_img == np.arange(len(txt)) if kind == 'caption' else labels[pick_img] == np.arange(len(txt))
    result['mixed_R1'] = float(100 * np.mean(wins & correct))
    result['CG'] = float(np.linalg.norm(img.mean(0) - txt.mean(0)))
    result['DG'] = float(np.hypot(result['CG'], np.linalg.norm(img.std(0) - txt.std(0))))
    return result

def stats(values):
    a = np.asarray(values, float)
    return dict(n=len(a), mean=float(a.mean()), sd=float(a.std(ddof=1)), minimum=float(a.min()), q025=float(np.quantile(a, 0.025)), median=float(np.median(a)), q975=float(np.quantile(a, 0.975)), maximum=float(a.max()))

def summary(target, values):
    a = np.asarray(values, float)
    return dict(targeted_effect=float(target), placebo=stats(a), targeted_minus_placebo=stats(float(target) - a), fraction_placebo_le_target=float(np.mean(a <= target)), fraction_placebo_ge_target=float(np.mean(a >= target)))

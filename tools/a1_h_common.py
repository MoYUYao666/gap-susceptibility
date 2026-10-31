"""Shared helpers for the A1 hardening scripts (items 1-5).

Contains / re-exports the two estimators that must stay byte-compatible across items:

  * `per_image_tau` -- per-image Kendall tau_b over a given frozen top-k index set, exactly the
    estimator of the archived `tools/clip_a1_probe2.py::kendall_topk` (tie-corrected, images with
    a zero-variance score vector dropped), but vectorised and returned per image so that the same
    array feeds both the point estimate and a bootstrap.
  * `kendall_topk`   -- the scalar mean of that array, with the archived skip rule.
  * `bootstrap_mean` -- percentile bootstrap over images with replacement.

Import: `from tools.a1_h_common import ...` is NOT used; the scripts add the repo root to sys.path
and import `a1_h_common` only when copied next to them. Instead each script contains its own copy
of these 40 lines to stay standalone -- this module exists as the single readable reference and is
imported by `tools/a1_h_bootstrap.py` and `tools/a1_h_offset.py` via an explicit sys.path insert.
"""
import numpy as np


def per_image_tau(base_np, cur_np, topk):
    """Per-image Kendall tau_b over the frozen top-k sets (double precision).

    `topk` is an (n, k) integer index array (the frozen top-k class set of each image).
    Returns a float array of length n; `nan` exactly where the archived scipy estimator skips
    the image (zero variance in either score vector). Requires k >= 2.
    """
    k = topk.shape[1]
    if k < 2:
        return None
    n0 = k * (k - 1) // 2
    r1 = np.take_along_axis(base_np, topk, axis=1).astype(np.float64)
    r2 = np.take_along_axis(cur_np, topk, axis=1).astype(np.float64)
    up = np.triu(np.ones((k, k), dtype=bool), 1)
    a = r1[:, :, None] - r1[:, None, :]
    b = r2[:, :, None] - r2[:, None, :]
    af, bf = a[:, up], b[:, up]
    cmd = np.sign(af * bf).sum(axis=1)
    n1 = (af == 0).sum(axis=1)
    n2 = (bf == 0).sum(axis=1)
    denom = np.sqrt((n0 - n1).astype(float) * (n0 - n2).astype(float))
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.where(denom > 1e-12, cmd / denom, np.nan)
    # clamp to the mathematically valid tau_b range; float32 score vectors can otherwise produce
    # |tau| marginally above 1 through the tie-correction denominator. Never changes a true value.
    return np.clip(t, -1.0, 1.0)


def kendall_topk(base_np, cur_np, topk):
    """Scalar mean of `per_image_tau` with the archived skip rule; (None, 0) if nothing scored."""
    pi = per_image_tau(base_np, cur_np, topk)
    if pi is None:
        return None, 0
    fin = pi[np.isfinite(pi)]
    if fin.size == 0:
        return None, 0
    return float(fin.mean()), int(fin.size)


def bootstrap_mean(per_image, n_boot=2000, seed=12345, alpha=0.05, chunk=200):
    """Percentile bootstrap of the mean of `per_image` (nan-aware, resampling images).

    Returns a dict with the point estimate, the bootstrap SE, and the (alpha/2, 1-alpha/2)
    percentile interval. Resampling is over images with replacement, which is the correct unit
    here because tau is a mean of per-image quantities. The replicates are drawn in chunks from a
    single RandomState, so the result is reproducible for a given (seed, n_boot, chunk).
    """
    a = np.asarray(per_image, dtype=np.float64)
    a = a[np.isfinite(a)]
    n = a.size
    if n == 0:
        return {'n_images': 0, 'point': None, 'se': None, 'ci_low': None, 'ci_high': None}
    rng = np.random.RandomState(seed)
    means = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        m = min(chunk, n_boot - done)
        idx = rng.randint(0, n, size=(m, n))
        means[done:done + m] = a[idx].mean(axis=1)
        done += m
    return {
        'n_images': int(n),
        'n_boot': int(n_boot),
        'point': float(a.mean()),
        'se': float(means.std(ddof=1)),
        'ci_low': float(np.percentile(means, 100 * alpha / 2)),
        'ci_high': float(np.percentile(means, 100 * (1 - alpha / 2))),
        'ci_level': 1 - alpha,
    }

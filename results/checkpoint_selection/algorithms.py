"""Pure numeric checkpoint analysis functions extracted from the archived audit."""
import itertools
import numpy as np

PROXIES = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]

READOUTS = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]

COORDINATES = ["classification_top1", "R1_t2i", "ARI_clipped"]

WEIGHTS = np.array([.5, .25, .25])

DELTAS = [0., .001, .0025, .005, .01, .02, .05]

TOL = 1e-12

MATCH_FIELDS = ["dataset", "tower", "rank", "seed", "split_seed", "epochs",
                "n_train", "n_test", "n_classes", "lr", "target", "trainable_tensors"]

SPECS = [
    ("b32_primary", ["runs"], "clip-b32", [8, 16, 32, 64], [45, 46], [47, 48]),
    ("b16_r8", ["runs_b16"], "clip-b16", [8], [45, 46], [47, 48]),
    ("b16_r16", ["runs_b16_r16"], "clip-b16", [16], [45, 46], [47, 48]),
    ("b16_r32", ["runs_b16_r32"], "clip-b16", [32], [45, 46], [47, 48]),
    ("b16_r64", ["runs_b16_r64"], "clip-b16", [64], [45, 46], [47, 48]),
    ("b32_r6", ["runs_b32_r6_full"], "clip-b32", [6], [45, 46], [47, 48]),
    ("b32_r12", ["runs_b32_r12_full"], "clip-b32", [12], [45, 46], [47, 48]),
    ("b32_r24", ["runs_b32_r24_full"], "clip-b32", [24], [45, 46], [47, 48]),
    ("b32_r48", ["runs_b32_r48_full"], "clip-b32", [48], [45, 46], [47, 48]),
    ("b32_split2_r16", ["runs_b32_split2_full"], "clip-b32", [16], [49, 50], [51, 52]),
    ("siglip_r8", ["runs_siglip_r8_dtd", "runs_siglip_r8_other"],
     "siglip-b16", [8], [45, 46], [47, 48]),
]

def normalize_readout(values):
    x = np.asarray(values, dtype=float)
    if x.shape != (4,) or not np.isfinite(x).all():
        raise ValueError("Missing or nonfinite readout")
    if np.any(x[:3] < 0) or np.any(x[:3] > 100) or not -1 <= x[3] <= 1:
        raise ValueError("Readout outside its documented raw range")
    return np.array([x[0] / 100, x[1] / 100, x[2] / 100, np.clip(x[3], 0, 1)])

def parse_run(data, member):
    try:
        meta = data["run"]
        epochs = sorted(data["epochs"], key=lambda e: e["epoch"])
        if [e["epoch"] for e in epochs] != [1, 2, 3] or meta["epochs"] != 3:
            raise ValueError("Exactly epochs 1,2,3 are required")
        for key in MATCH_FIELDS + ["backbone"]:
            if key not in meta:
                raise ValueError(f"Missing run metadata: {key}")
        cond = [e["conditions"]["original"] for e in epochs]
        raw = np.array([[c[k] for k in READOUTS] for c in cond], dtype=float)
        readouts = np.array([normalize_readout(row) for row in raw])
        proxies = np.array([[c[k] for k in PROXIES] for c in cond], dtype=float)
        if not np.isfinite(proxies).all():
            raise ValueError("Nonfinite proxy")
        return {"member": member, "meta": dict(meta), "raw": raw,
                "readouts": readouts, "proxies": proxies}
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(f"Malformed input {member}: {error}") from error

def select_index(run, pi, sign):
    return int(np.argmax(sign * run["proxies"][:, pi]))

def choose_sign(cal, pi):
    if not cal:
        raise ValueError("Empty calibration set")
    def mean_regret(sign):
        return np.mean([r["readouts"].mean(axis=1).max() -
                        r["readouts"].mean(axis=1)[select_index(r, pi, sign)] for r in cal])
    return 1 if mean_regret(1) <= mean_regret(-1) else -1

def partition_loss(losses, delta):
    x = np.asarray(losses, dtype=float)
    worse = x > delta + TOL
    better = x < -delta - TOL
    return {"delta": delta, "n": len(x), "worse": int(worse.sum()),
            "better": int(better.sum()), "within": int((~(worse | better)).sum()),
            "positive_loss_sum": float(np.maximum(x, 0).sum()),
            "positive_gain_sum": float(np.maximum(-x, 0).sum()),
            "mean_loss": float(x.mean())}

def nearest_zero_weights(component_mean):
    """Exact small-dimensional vertex enumeration of a convex piecewise-linear problem."""
    a = np.asarray(component_mean, dtype=float)
    if abs(a @ WEIGHTS) <= TOL:
        return {"l1_distance": 0., "weights": WEIGHTS.tolist()}
    if a.min() > TOL or a.max() < -TOL:
        return None
    candidates = []
    # Intersect sum(w)=1 and a.w=0 with each boundary w_j=0 or L1 kink w_j=w0_j.
    for j, value in itertools.product(range(3), [0, 1]):
        axis = np.eye(3)[j]
        mat = np.vstack([np.ones(3), a, axis])
        if abs(np.linalg.det(mat)) < 1e-15:
            continue
        w = np.linalg.solve(mat, [1, 0, 0 if value == 0 else WEIGHTS[j]])
        if np.all(w >= -TOL) and np.all(w <= 1 + TOL):
            candidates.append(w)
    if not candidates:
        raise ValueError("Zero-plane geometry produced no feasible vertex")
    w = min(candidates, key=lambda v: float(abs(v - WEIGHTS).sum()))
    return {"l1_distance": float(abs(w - WEIGHTS).sum()), "weights": w.tolist()}

def preference_summary(component_losses):
    x = np.asarray(component_losses, dtype=float)
    a = x.mean(axis=0)
    low, high = int(np.argmin(a)), int(np.argmax(a))
    blo, bhi = np.full(3, .2), np.full(3, .2)
    blo[low] += .4
    bhi[high] += .4
    dominates = np.all(x >= -TOL, axis=1) & np.any(x > TOL, axis=1)
    improves = np.all(x <= TOL, axis=1) & np.any(x < -TOL, axis=1)
    identical = np.all(abs(x) <= TOL, axis=1)
    return {
        "component_mean_loss": a.tolist(), "original_mean_loss": float(a @ WEIGHTS),
        "equal_distinct_mean_loss": float(a.mean()),
        "full_simplex_range": [float(a.min()), float(a.max())],
        "full_simplex_min_weights": np.eye(3)[low].tolist(),
        "full_simplex_max_weights": np.eye(3)[high].tolist(),
        "balanced_simplex_range": [float(a @ blo), float(a @ bhi)],
        "balanced_simplex_min_weights": blo.tolist(),
        "balanced_simplex_max_weights": bhi.tolist(),
        "nearest_zero_from_original": nearest_zero_weights(a),
        "pareto_counts": {"last_weakly_dominates": int(dominates.sum()),
                          "proxy_weakly_dominates": int(improves.sum()),
                          "tradeoff": int((~(dominates | improves | identical)).sum()),
                          "identical": int(identical.sum())},
    }

def match_records(left, right):
    def mapping(rows):
        out = {}
        for r in rows:
            key = tuple(r["meta"][k] for k in ["dataset", "tower", "rank", "seed"])
            if key in out:
                raise ValueError("Duplicate matching key")
            out[key] = r
        return out
    a, b = mapping(left), mapping(right)
    if a.keys() != b.keys():
        raise ValueError("Incomplete matched contrast")
    result = []
    for key in sorted(a):
        if any(a[key]["meta"][k] != b[key]["meta"][k] for k in MATCH_FIELDS):
            raise ValueError(f"Unmatched training/data metadata: {key}")
        result.append((a[key], b[key]))
    return result

def cluster_ci(values, runs):
    labels = [r["meta"]["dataset"] + "|" + r["meta"]["tower"] for r in runs]
    groups = sorted(set(labels))
    arrays = [np.array([v for v, label in zip(values, labels) if label == u]) for u in groups]
    # Sums/counts preserve the original ratio estimator for unequal cluster sizes too.
    sums = np.array([x.sum() for x in arrays])
    counts = np.array([len(x) for x in arrays])
    draws = np.random.default_rng(20261115).integers(0, len(groups), (10000, len(groups)))
    boots = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return {"mean": float(np.mean(values)), "ci95_cluster": np.quantile(boots, [.025, .975]).tolist(),
            "n": len(values), "n_clusters": len(groups), "cluster_names": groups,
            "cluster_sizes": counts.tolist(), "n_boot": 10000, "seed": 20261115,
            "interpretation": "descriptive; conditional on calibration; not simultaneous"}

# -*- coding: utf-8 -*-
r"""Purely-local analysis extensions: exact permutation for r=3 vs r=8 and a 10k bootstrap of the environment
variance share."""
import glob
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def blank(rank):
    vals = []
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*.json" % rank)):
        n = os.path.basename(f)
        if any(x in n for x in ("partial", "imgs", "_e1_")):
            continue
        v = json.load(io.open(f, encoding="utf-8")).get("delta_E")
        if v is not None:
            vals.append(float(v))
    return vals


def main() -> int:
    r3, r8 = blank(3), blank(8)
    obs = abs(np.mean(r3) - np.mean(r8))
    pool = r3 + r8
    rng = np.random.default_rng(42)
    ge = 0
    n_perm = 184756  # all 10-of-20 splits
    # exhaustive exact permutation over all splits
    from itertools import combinations
    for idx in combinations(range(20), 10):
        a = [pool[i] for i in idx]
        b = [pool[i] for i in range(20) if i not in idx]
        if abs(np.mean(a) - np.mean(b)) >= obs - 1e-12:
            ge += 1
    p = ge / n_perm
    out1 = {"meta": {"script": "tools/_p1565_quick_stats.py", "test": "exact two-sided permutation r=3 vs r=8",
                     "n3": len(r3), "n8": len(r8), "n_perm": n_perm},
            "mean3": float(np.mean(r3)), "mean8": float(np.mean(r8)), "p": float(p)}
    json.dump(out1, io.open(os.path.join(AN, "p3_perm_r3_r8.json"), "w", encoding="utf-8"), indent=1)
    print("perm r3 vs r8: p=%.3g (obs %.1f)" % (p, obs))

    # environment variance bootstrap (10k) over seed resampling within each environment
    env1 = json.load(io.open(os.path.join(AN, "p3_rerun_protocol.json"), encoding="utf-8"))["runs"]
    env = {"torch29": [env1["r5_s42"]["delta_E"]]}
    # use all torch2.9 r=5 seeds from the seed archive
    seeds = json.load(io.open(os.path.join(AN, "p3_seeds_combined.json"), encoding="utf-8"))["values"]["r5"]
    env["torch29"] = [float(v) for v in seeds.values()]
    env["torch212"] = blank(5)
    env["torch24"] = [json.load(io.open(f, encoding="utf-8"))["delta_E"]
                      for f in sorted(glob.glob(os.path.join(EXP, "verify_r5_s*_a10.json")))]
    rng = np.random.default_rng(7)
    shares = []
    for _ in range(10000):
        means, vars_ = [], []
        for vals in env.values():
            arr = np.array(vals)
            m = np.array([rng.choice(arr) for _ in range(len(arr))]).mean()
            means.append(m)
            vars_.append(arr.var(ddof=1))
        means = np.array(means)
        sig2_env = max(0.0, means.var(ddof=1) - np.mean(vars_))
        sig2_seed = np.mean(vars_)
        shares.append(sig2_env / (sig2_env + sig2_seed) if sig2_env + sig2_seed > 0 else 0.0)
    out2 = {"meta": {"script": "tools/_p1565_quick_stats.py", "test": "bootstrap environment variance share",
                     "n_boot": 10000},
            "env_n": {k: len(v) for k, v in env.items()},
            "share_mean": float(np.mean(shares)),
            "share_ci95": [float(np.percentile(shares, 2.5)), float(np.percentile(shares, 97.5))]}
    json.dump(out2, io.open(os.path.join(AN, "p3_env_variance_boot.json"), "w", encoding="utf-8"), indent=1)
    print("env share 10k bootstrap: %.2f [%.2f, %.2f]" % (out2["share_mean"], *out2["share_ci95"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

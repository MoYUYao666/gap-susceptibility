# -*- coding: utf-8 -*-
"""Recompute the environment-vs-seed variance decomposition with the four torch2.4 seeds and the 10k bootstrap."""
import glob
import io
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")

seeds = json.load(io.open(os.path.join(AN, "p3_seeds_combined.json"), encoding="utf-8"))["values"]["r5"]
env1 = [float(v) for v in seeds.values()]
env2 = []
for f in glob.glob(os.path.join(EXP, "cloud_verify_r5_s*.json")):
    n = os.path.basename(f)
    if any(x in n for x in ("partial", "imgs", "_e1_")):
        continue
    v = json.load(io.open(f, encoding="utf-8")).get("delta_E")
    if v is not None:
        env2.append(float(v))
env3 = [json.load(io.open(f, encoding="utf-8"))["delta_E"]
        for f in sorted(glob.glob(os.path.join(EXP, "verify_r5_s*_a10*.json")))]
envs = {"torch 2.9/cu130": env1, "torch 2.12/cu130": env2, "torch 2.4/cu121": env3}


def decomposition(vals_by_env):
    k = len(vals_by_env)
    allv = [x for v in vals_by_env.values() for x in v]
    n = len(allv)
    grand = float(np.mean(allv))
    ssb = sum(len(v) * (float(np.mean(v)) - grand) ** 2 for v in vals_by_env.values())
    ssw = sum(sum((x - float(np.mean(v))) ** 2 for x in v) for v in vals_by_env.values())
    dfb = k - 1
    dfw = n - k
    msb = ssb / dfb
    msw = ssw / dfw
    n0 = (n - sum(len(v) ** 2 for v in vals_by_env.values()) / n) / (k - 1)
    sig2_env = max(0.0, (msb - msw) / n0)
    sig2_seed = msw
    share = sig2_env / (sig2_env + sig2_seed) if sig2_env + sig2_seed > 0 else 0.0
    return float(np.sqrt(sig2_env)), float(np.sqrt(sig2_seed)), share


se, ss, share = decomposition(envs)
rng = np.random.default_rng(7)
shares = []
for _ in range(10000):
    vals = {k: [float(x) for x in rng.choice(v, len(v))] for k, v in envs.items()}
    _, _, sh = decomposition(vals)
    shares.append(sh)
out = {"meta": {"script": "tools/_p1570_env_variance_update.py", "n_boot": 10000,
                "method": "one-way random-effects ANOVA on environment level, seed bootstrap within environment"},
       "envs": {k: {"n": len(v), "mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "values": v}
                for k, v in envs.items()},
       "sigma_env": se, "sigma_seed": ss, "env_share": share,
       "bootstrap": {"share_mean": float(np.mean(shares)),
                     "share_ci95": [float(np.percentile(shares, 2.5)), float(np.percentile(shares, 97.5))]}}
json.dump(out, io.open(os.path.join(AN, "p3_env_variance.json"), "w", encoding="utf-8"), indent=1)
print({k: (len(v), round(float(np.mean(v)), 1)) for k, v in envs.items()})
print("sigma_env %.1f sigma_seed %.1f share %.2f CI [%.2f, %.2f]" % (
    se, ss, share, *out["bootstrap"]["share_ci95"]))

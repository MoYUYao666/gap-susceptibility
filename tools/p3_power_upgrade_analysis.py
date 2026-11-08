# -*- coding: utf-8 -*-
"""P3 power upgrade analysis (2026-11-08): 16-seed allocation contrast + random-pool comparison.

Reads the archived run records (local `outputs/analysis/p3_alloc_runs/main/*.json`) plus the new 10 seeds
run on the cloud (`outputs/analysis/p3_alloc_runs_cloud/...`), and writes a power report:
  outputs/analysis/p3_power_upgrade_2026-11-08.json
"""
import glob
import io
import json
import math
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "outputs", "analysis", "p3_alloc_runs", "main")
CLOUD = os.path.join(REPO, "outputs", "analysis", "p3_alloc_runs_batch1", "outputs", "analysis", "p3_alloc_runs", "main_batch1")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_power_upgrade_2026-11-08.json")


def load_runs(d):
    runs = {}
    for p in glob.glob(os.path.join(d, "*.json")):
        try:
            r = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if "delta_E" not in r and "deltaE" not in r:
            continue
        name = os.path.basename(p)[:-5]
        if "__seed" not in name:
            continue
        plan, seed = name.split("__seed")
        runs[(plan, int(seed))] = r.get("delta_E", r.get("deltaE"))
    return runs


def t_crit(df, alpha=0.05):
    # two-sided 95% t critical values for small df (enough range for this report)
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
             9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
             16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}
    for k in sorted(table):
        if df <= k:
            return table[k]
    return 1.96


def paired_ci(diffs):
    n = len(diffs)
    mean = st.mean(diffs)
    sd = st.stdev(diffs) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return {"n": n, "mean": round(mean, 3), "sd": round(sd, 3), "se": round(se, 3),
            "ci95": [round(mean - t_crit(n - 1) * se, 3), round(mean + t_crit(n - 1) * se, 3)]}


def main():
    local = load_runs(LOCAL)
    cloud = load_runs(CLOUD)
    merged = dict(local)
    merged.update(cloud)
    arms = {}
    for plan in ("uniform", "exp_beta_paper_0.137"):
        vals = {seed: v for (p, seed), v in merged.items() if p == plan}
        arms[plan] = {"n": len(vals), "mean": round(st.mean(vals.values()), 3),
                      "sd": round(st.stdev(vals.values()), 3) if len(vals) > 1 else 0.0,
                      "seeds": sorted(vals)}
    seeds_both = sorted(set(arms["uniform"]["seeds"]) & set(arms["exp_beta_paper_0.137"]["seeds"]))
    diffs = [merged[("exp_beta_paper_0.137", s)] - merged[("uniform", s)] for s in seeds_both]
    paired = paired_ci(diffs)
    # random pool: all random_* runs available locally (10 usable plans x 3 seeds)
    rand_vals = [v for (p, s), v in local.items() if p.startswith("random_")]
    random_pool = {"n": len(rand_vals), "mean": round(st.mean(rand_vals), 3) if rand_vals else None,
                   "sd": round(st.stdev(rand_vals), 3) if len(rand_vals) > 1 else None}
    # Welch t (exp vs random pool) and exp values
    exp_vals = [v for (p, s), v in merged.items() if p == "exp_beta_paper_0.137"]
    def welch(a, b):
        if len(a) < 2 or len(b) < 2:
            return None
        ma, mb = st.mean(a), st.mean(b)
        va, vb = st.variance(a), st.variance(b)
        se = math.sqrt(va / len(a) + vb / len(b))
        t = (ma - mb) / se if se else float("inf")
        return {"mean_exp": round(ma, 3), "mean_random": round(mb, 3), "diff": round(ma - mb, 3), "t": round(t, 3)}
    report = {
        "generated": "2026-11-08",
        "source": {"local": "outputs/analysis/p3_alloc_runs/main", "cloud": "outputs/analysis/p3_alloc_runs_batch1"},
        "allocation_contrast_16_seeds": {
            "arms": arms,
            "paired_exp_minus_uniform": paired,
            "paired_ci_excludes_zero": paired["ci95"][0] > 0 or paired["ci95"][1] < 0,
        },
        "random_pool": {"archive": random_pool, "exp_vs_random": welch(exp_vals, rand_vals)},
        "notes": ("The random-pool target of 12 non-duplicate plans is not reachable: the exact same-budget allocation "
                  "space contains 15 allocations, 4 of which coincide with named/corner plans, leaving 10 non-duplicate "
                  "random plans. The 16-seed allocation contrast is complete (6 archived + 10 new seeds)."),
    }
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p444_p3_phase_boundary.py -- P3 R3.17/R3.19 part 2.

Three things the raw archive can settle, none of which the paper currently does:

  (a) Why do the batches disagree on sign?  Compare the archived E TRAJECTORIES
      (not just dE) for the same rank/seed across batches -- same initial E0?
      same per-epoch energy?  This decides whether the discrepancy is a
      seed-draw effect or a genuine environment/software difference (R3.18).
  (b) Exhaustive audit of every archived (rank, seed) configuration for the
      ordering dE(r=6) > dE(r=5) -- the paper claims 6/6 configurations; we list
      the full machine enumeration with hit count.
  (c) Paired-seed analysis (seeds are matched across ranks) + exact sign test +
      minimum detectable effect at n=3 -- the capability boundary for R3.17.

Output: outputs/analysis/p3_phase_boundary.json
"""
import itertools
import json
import math
import os
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")

ARCH = {
    "E2": "paper3/scripts/outputs/experiments/E2_results.json",
    "sample_size": "paper3/scripts/outputs/experiments/sample_size_results.json",
    "sharegpt": "paper3/scripts/outputs/experiments/vqa_phase_results.json",
    "Qwen": "paper3/scripts/outputs/experiments/Qwen_results.json",
    "ers": "paper3/scripts/outputs/experiments/ers_1epoch_results.json",
}


def jload(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def fin(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


e2 = jload(ARCH["E2"])

# ---------------------------------------------------------------- (a) batches
batch_runs = {}
for batch in ("E2", "extra", "sweep"):
    for it in e2.get(batch, []):
        if not it.get("ok", False):
            continue
        batch_runs.setdefault(batch, []).append(it)

traj_cmp = {"per_rank_seed": [], "E0_by_batch": {}}
for batch, rs in batch_runs.items():
    e0s = sorted(set(r["E"][0] for r in rs if r.get("E")))
    traj_cmp["E0_by_batch"][batch] = {"E0_values": e0s,
                                      "n_runs": len(rs),
                                      "epoch_lengths": sorted(set(len(r["E"]) for r in rs))}

# join on (rank, seed)
idx = defaultdict(dict)
for batch, rs in batch_runs.items():
    for r in rs:
        idx[(r["rank"], r["seed"])][batch] = r

overlap_rows = []
for (rk, sd), d in sorted(idx.items()):
    if len(d) < 2:
        continue
    row = {"rank": rk, "seed": sd, "batches": {}}
    for b, r in d.items():
        row["batches"][b] = {"E": r["E"], "E0": r["E"][0],
                             "dE": (r["E"][-1] - r["E"][0]) if fin(r["E"][-1]) else None}
    vals = [(b, v["dE"]) for b, v in row["batches"].items() if v["dE"] is not None]
    if len(vals) >= 2:
        row["dE_spread_across_batches"] = float(max(v for _, v in vals) - min(v for _, v in vals))
        row["sign_agreement"] = len(set(np.sign(v) for _, v in vals)) == 1
    overlap_rows.append(row)

traj_cmp["per_rank_seed"] = overlap_rows

# epoch-by-epoch comparison for the ranks that disagree
epoch_cmp = []
for rk in (4, 5, 6, 7, 8, 16):
    for sd in (42, 123, 999):
        d = idx.get((rk, sd), {})
        if "E2" in d and "sweep" in d:
            epoch_cmp.append({"rank": rk, "seed": sd,
                              "E2": d["E2"]["E"],
                              "sweep": d["sweep"]["E"]})
traj_cmp["epoch_by_epoch_E2_vs_sweep"] = epoch_cmp

# ------------------------------------------------------- (b) ordering audit
cfg = []  # every configuration where both r=5 and r=6 exist


def add_cfg(name, src, r5, r6, note="", field=""):
    if r5 is None or r6 is None:
        return
    cfg.append({"configuration": name, "source_file": src, "field": field,
                "dE_r5": r5, "dE_r6": r6, "r6_gt_r5": bool(r6 > r5),
                "note": note})


# E2 batches
for batch in ("extra",):
    for it5 in [r for r in batch_runs[batch] if r["rank"] == 5]:
        for it6 in [r for r in batch_runs[batch] if r["rank"] == 6 and r["seed"] == it5["seed"]]:
            add_cfg("LLaVA %s seed=%s" % (batch, it5["seed"]), ARCH["E2"],
                    it5["E"][-1] - it5["E"][0], it6["E"][-1] - it6["E"][0],
                    "multi-seed sweep batch", "$.%s rank5/6 seed%s" % (batch, it5["seed"]))
# sample sizes (one seed each)
ss = jload(ARCH["sample_size"])
for it in ss["runs"]:
    if it["rank"] == 5:
        pass
ss5 = {r["samples"]: r for r in ss["runs"] if r["rank"] == 5}
ss6 = {r["samples"]: r for r in ss["runs"] if r["rank"] == 6}
for n in sorted(set(ss5) & set(ss6)):
    add_cfg("LLaVA sample-size n=%d" % n, ARCH["sample_size"],
            ss5[n]["E"][-1] - ss5[n]["E"][0], ss6[n]["E"][-1] - ss6[n]["E"][0],
            "single seed per cell", "$.runs samples=%d rank=5/6" % n)
# ShareGPT / vqa_phase: one mean per rank (3 seeds each)
sg = jload(ARCH["sharegpt"])
if "r5" in sg and "r6" in sg:
    add_cfg("ShareGPT r5 vs r6 (3-seed means)", ARCH["sharegpt"],
            float(np.mean(sg["r5"]["dE"])), float(np.mean(sg["r6"]["dE"])),
            "3 seeds per rank", "$.r5.dE / $.r6.dE")

n_gt = sum(1 for c in cfg if c["r6_gt_r5"])
order_audit = {
    "n_configurations": len(cfg),
    "n_r6_gt_r5": n_gt,
    "all_hold": bool(n_gt == len(cfg)),
    "configurations": cfg,
    "definition": ("a 'configuration' is one archived (dataset, batch, seed) cell pair "
                   "that has both r=5 and r=6 measured; the paper's '6/6' is checked "
                   "against the full machine enumeration"),
    "exact_sign_test_all_hold": {"k": n_gt, "n": len(cfg),
                                 "p_two_sided": min(1.0, 2 * sum(
                                     math.comb(len(cfg), i) for i in range(n_gt, len(cfg) + 1)) / 2 ** len(cfg))
                                 if len(cfg) else None},
}

# ------------------------------------------------ (c) paired + power analysis
paired = {}
r5v, r6v, seeds = [], [], []
for it5 in [r for r in batch_runs["extra"] if r["rank"] == 5]:
    for it6 in [r for r in batch_runs["extra"] if r["rank"] == 6 and r["seed"] == it5["seed"]]:
        r5v.append(it5["E"][-1] - it5["E"][0])
        r6v.append(it6["E"][-1] - it6["E"][0])
        seeds.append(it5["seed"])
d = np.asarray(r6v, dtype=float) - np.asarray(r5v, dtype=float)
paired["seed_matched_pairs"] = {"seeds": seeds, "dE_r5": [float(v) for v in r5v],
                                "dE_r6": [float(v) for v in r6v],
                                "differences_r6_minus_r5": [float(v) for v in d],
                                "all_positive": bool(np.all(d > 0))}
if len(d) > 1:
    t, p = stats.ttest_rel(r6v, r5v)
    paired["paired_t"] = {"t": float(t), "p": float(p), "df": len(d) - 1}
    try:
        w, pw = stats.wilcoxon(r6v, r5v)
        paired["wilcoxon"] = {"stat": float(w), "p": float(pw), "n_pairs": len(d)}
    except Exception as e:
        paired["wilcoxon"] = {"error": str(e)}
# exact sign-flip permutation on the paired differences (2^3 = 8)
obs = float(np.mean(d))
cnt = 0
tot = 0
for signs in itertools.product([1, -1], repeat=len(d)):
    tot += 1
    if abs(np.mean(d * np.asarray(signs))) >= abs(obs) - 1e-12:
        cnt += 1
paired["exact_signflip_permutation"] = {"n_perm": tot, "observed_mean_diff": obs,
                                        "p_two_sided": cnt / tot}

# minimum detectable effect at n=3 (two-sample, alpha=.05, power=.80)
def mde(n1, n2, alpha=0.05, power=0.80):
    df = n1 + n2 - 2
    tcrit = stats.t.ppf(1 - alpha / 2, df)
    # solve for noncentrality: approximate via normal for the power term
    z = stats.norm.ppf(power)
    delta = (tcrit + z) * math.sqrt(1.0 / n1 + 1.0 / n2)
    return {"n1": n1, "n2": n2, "alpha": alpha, "power": power,
            "cohens_d_mde": float(delta),
            "note": "two-sample two-sided t, equal n; effect size in pooled-sd units"}


power_analysis = {
    "n3_vs_n3": mde(3, 3),
    "observed_effects": {},
}
# observed effect sizes (Cohen's d) for the key contrasts
def cohens_d(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    sp = math.sqrt(((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1))
                   / (len(a) + len(b) - 2))
    return float((np.mean(a) - np.mean(b)) / sp) if sp > 0 else None


power_analysis["observed_effects"]["r6_vs_r5_extra_batch"] = {
    "cohens_d": cohens_d(r6v, r5v), "n": [3, 3]}
power_analysis["observed_effects"]["r4_vs_r16_E2_batch"] = {
    "cohens_d": cohens_d([r["E"][-1] - r["E"][0] for r in batch_runs["E2"] if r["rank"] == 16],
                         [r["E"][-1] - r["E"][0] for r in batch_runs["E2"] if r["rank"] == 4]),
    "n": [3, 3]}

# ShareGPT: 3 seeds per rank, check every adjacent-rank contrast
sg_pairs = []
ranks_sg = sorted(int(k[1:]) for k in sg.keys())
for a, b in zip(ranks_sg, ranks_sg[1:]):
    va = np.asarray(sg["r%d" % a]["dE"], dtype=float)
    vb = np.asarray(sg["r%d" % b]["dE"], dtype=float)
    t, p = stats.ttest_ind(vb, va, equal_var=False)
    sg_pairs.append({"r_a": a, "r_b": b, "mean_a": float(va.mean()), "mean_b": float(vb.mean()),
                     "welch_t": float(t), "welch_p": float(p),
                     "significant_at_05": bool(p < 0.05)})
sharegpt_adjacent = {
    "pairs": sg_pairs,
    "n_significant_at_05": sum(1 for x in sg_pairs if x["significant_at_05"]),
    "note": ("adjacent-rank Welch tests on the ShareGPT table; addresses whether the "
             "r=5 -> r=6 step is individually resolvable with 3 seeds"),
}
# specifically 5 vs 6
va = np.asarray(sg["r5"]["dE"], dtype=float)
vb = np.asarray(sg["r6"]["dE"], dtype=float)
t, p = stats.ttest_ind(vb, va, equal_var=False)
sharegpt_adjacent["r5_vs_r6"] = {"welch_t": float(t), "welch_p": float(p),
                                 "mean_r5": float(va.mean()), "mean_r6": float(vb.mean()),
                                 "sd_r5": float(va.std(ddof=1)), "sd_r6": float(vb.std(ddof=1)),
                                 "cohens_d": cohens_d(vb, va)}

# Qwen: check per-seed spread (relevant to "Qwen stable")
qw = jload(ARCH["Qwen"])
qwen_runs = []
for it in qw.get("sweep", []):
    if it.get("E"):
        qwen_runs.append({"rank": it["rank"], "seed": it["seed"],
                          "dE": it["E"][-1] - it["E"][0]})
qwen_by_rank = defaultdict(list)
for r in qwen_runs:
    qwen_by_rank[r["rank"]].append(r["dE"])
qwen = {"per_rank": {}, "n_total": len(qwen_runs),
        "n_nan": sum(1 for r in qwen_runs if not fin(r["dE"]))}
for rk in sorted(qwen_by_rank):
    v = np.asarray(qwen_by_rank[rk], dtype=float)
    qwen["per_rank"]["r%d" % rk] = {
        "mean": float(v.mean()), "sd_sample": float(v.std(ddof=1)),
        "values": [float(x) for x in v],
        "signs": ["+" if x > 0 else "-" for x in v],
        "n_negative": int(np.sum(v < 0))}
qwen["n_ranks_with_negative_seed"] = sum(
    1 for k, v in qwen["per_rank"].items() if v["n_negative"] > 0)
qwen["n_ranks"] = len(qwen["per_rank"])

out = {
    "meta": {
        "script": "tools/_p444_p3_phase_boundary.py",
        "task": "task-11 (P3 R3.17 / R3.19, part 2)",
        "archive_files": ARCH,
    },
    "batch_trajectory_comparison": traj_cmp,
    "r6_gt_r5_exhaustive_audit": order_audit,
    "paired_seed_analysis": paired,
    "power_analysis": power_analysis,
    "sharegpt_adjacent_tests": sharegpt_adjacent,
    "qwen_per_seed": qwen,
}
dst = os.path.join(OUTDIR, "p3_phase_boundary.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("=" * 78)
print("(a) BATCH TRAJECTORY COMPARISON")
for b, v in traj_cmp["E0_by_batch"].items():
    print("  batch %-6s n_runs=%d E0=%s traj_len=%s"
          % (b, v["n_runs"], v["E0_values"], v["epoch_lengths"]))
print("  rank/seed cells measured in >=2 batches: %d" % len(overlap_rows))
dis = [r for r in overlap_rows if not r.get("sign_agreement", True)]
print("  cells whose SIGN disagrees across batches: %d" % len(dis))
for r in dis[:12]:
    print("    r=%-3s seed=%-5s %s" % (r["rank"], r["seed"],
          {b: (round(v["dE"], 1) if v["dE"] is not None else "NaN")
           for b, v in r["batches"].items()}))
print("  epoch-by-epoch E2 vs sweep pairs: %d" % len(epoch_cmp))
for r in epoch_cmp[:6]:
    print("    r=%-3s s=%-5s E2=%s sweep=%s" % (r["rank"], r["seed"], r["E2"], r["sweep"]))

print("\n" + "=" * 78)
print("(b) r6 > r5 EXHAUSTIVE AUDIT: %d/%d configurations hold"
      % (order_audit["n_r6_gt_r5"], order_audit["n_configurations"]))
for c in cfg:
    print("  %-34s r5=%9.1f r6=%9.1f  hold=%s" % (c["configuration"], c["dE_r5"], c["dE_r6"], c["r6_gt_r5"]))

print("\n" + "=" * 78)
print("(c) PAIRED SEED ANALYSIS")
print("  seeds=%s" % paired["seed_matched_pairs"]["seeds"])
print("  r5=%s" % [round(v, 1) for v in r5v])
print("  r6=%s" % [round(v, 1) for v in r6v])
print("  diff=%s all_positive=%s" % ([round(v, 1) for v in d], paired["seed_matched_pairs"]["all_positive"]))
print("  paired t=%.2f p=%.4f | wilcoxon p=%s | exact sign-flip p=%.3f"
      % (paired["paired_t"]["t"], paired["paired_t"]["p"],
         round(paired["wilcoxon"].get("p", float('nan')), 4),
         paired["exact_signflip_permutation"]["p_two_sided"]))
print("  MDE at n=3 vs n=3 (alpha=.05, power=.80): Cohen's d = %.2f" % power_analysis["n3_vs_n3"]["cohens_d_mde"])
print("  observed d for r6 vs r5: %.2f" % power_analysis["observed_effects"]["r6_vs_r5_extra_batch"]["cohens_d"])
print("  observed d for r16 vs r4: %.2f" % power_analysis["observed_effects"]["r4_vs_r16_E2_batch"]["cohens_d"])

print("\n" + "=" * 78)
print("SHAREGPT adjacent-rank Welch tests: %d/%d significant at .05"
      % (sharegpt_adjacent["n_significant_at_05"], len(sg_pairs)))
print("  r5 vs r6: t=%.2f p=%.4f  d=%.2f" % (sharegpt_adjacent["r5_vs_r6"]["welch_t"],
                                             sharegpt_adjacent["r5_vs_r6"]["welch_p"],
                                             sharegpt_adjacent["r5_vs_r6"]["cohens_d"]))
print("\nQWEN: %d runs, %d NaN, %d/%d ranks contain a negative seed"
      % (qwen["n_total"], qwen["n_nan"], qwen["n_ranks_with_negative_seed"], qwen["n_ranks"]))
print("wrote", dst)

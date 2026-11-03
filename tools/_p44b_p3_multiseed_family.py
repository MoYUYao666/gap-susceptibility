#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44b_p3_multiseed_family.py -- the 10-seed independent replication family.

tools/ap3_phase_stats_recompute.py (family B) discovers `verify_r{N}_s{M}.json`
files that follow the untagged reference protocol (epochs=3, no config tag).
There are 10 seeds for r=5 AND 10 for r=6 -- far more than the 3 seeds the
manuscript is based on.  This script characterises that family properly:

  * membership + provenance per file (path, E0, tainted flags)
  * homogeneous-subgroup check: are all 10 runs really one protocol?
    (E0 clusters, deltas vs E2/extra/sweep batches)
  * hardened statistics on the SUBSET that is protocol-homogeneous:
    mean, sample sd, bootstrap CI, MAD, worst case, sign test, exact
    paired-seed test, Welch, and a per-seed ordering audit
  * the direct comparison with the 3-seed numbers the paper uses

Everything is recomputed here; the family definition is re-derived rather than
imported, so this file is an independent check of ap3_phase_stats_recompute.py.

Output: outputs/analysis/p3_multiseed_family.json
"""
import glob
import itertools
import json
import math
import os
import re
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")
EXP = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments")

BOOT_N = 20000
BOOT_SEED = 20261012


def fin(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ---- family discovery: untagged reference-protocol verify_rN_sM.json
members = []
for p in sorted(glob.glob(os.path.join(EXP, "verify_r*_s*.json"))):
    fn = os.path.basename(p)
    if not re.match(r"^verify_r\d+_s\d+\.json$", fn):
        continue
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    E = d.get("E", [])
    if d.get("epochs") != 3 or len(E) < 2:
        continue
    members.append({
        "file": "paper3/scripts/outputs/experiments/" + fn,
        "rank": int(d["rank"]), "seed": int(d["seed"]),
        "E": E, "E0": E[0], "dE": (E[-1] - E[0]) if (fin(E[-1]) and fin(E[0])) else None,
        "delta_E_field": d.get("delta_E"),
        "note": d.get("note"),
        "epochs": d.get("epochs"), "num_samples": d.get("num_samples"),
        "lr": d.get("lr"), "opt": d.get("opt"), "compute_dtype": d.get("compute_dtype"),
        "warmup": d.get("warmup"),
    })

by_rank = defaultdict(list)
for m in members:
    by_rank[m["rank"]].append(m)
fam = {r: sorted(v, key=lambda x: x["seed"]) for r, v in by_rank.items()}
family = {
    "n_files": len(members),
    "ranks": {str(r): {"n_seeds": len(v), "seeds": [x["seed"] for x in v],
                       "E0_values": sorted(set(x["E0"] for x in v)),
                       "files": [x["file"] for x in v]} for r, v in sorted(fam.items())},
}

# ---- E0 clustering: is the family protocol-homogeneous?
e0_hist = defaultdict(list)
for m in members:
    e0_hist[(m["rank"], m["E0"])].append(m["seed"])
family["E0_clusters"] = {"%s@%s" % (k[0], k[1]): v for k, v in sorted(e0_hist.items())}
family["E0_homogeneous_per_rank"] = {
    str(r): (len(set(x["E0"] for x in v)) == 1) for r, v in sorted(fam.items())}


def desc(x, label, sources=None):
    x = np.asarray([v for v in x if fin(v)], dtype=float)
    if x.size == 0:
        return None
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, x.size, size=(BOOT_N, x.size))
    bs = x[idx].mean(axis=1)
    med = np.median(x)
    out = {
        "label": label, "n": int(x.size), "values": [float(v) for v in x],
        "mean": float(x.mean()),
        "sd_sample": float(x.std(ddof=1)) if x.size > 1 else None,
        "sd_population": float(x.std(ddof=0)),
        "median": float(med),
        "mad": float(np.median(np.abs(x - med))),
        "iqr": float(np.percentile(x, 75) - np.percentile(x, 25)),
        "min": float(x.min()), "max": float(x.max()),
        "range": float(x.max() - x.min()),
        "n_positive": int((x > 0).sum()), "n_negative": int((x < 0).sum()),
        "mean_boot_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
        "bootstrap_n": BOOT_N, "bootstrap_seed": BOOT_SEED,
    }
    if x.size > 1:
        t, p = stats.ttest_1samp(x, 0.0)
        out["t_vs_zero"] = {"t": float(t), "p": float(p), "df": int(x.size - 1)}
        ci = stats.t.interval(0.95, x.size - 1, loc=x.mean(), scale=stats.sem(x))
        out["mean_t_ci95"] = [float(ci[0]), float(ci[1])]
        # exact sign test
        k = int((x > 0).sum())
        n = int(x.size)
        out["sign_test"] = {
            "k_positive": k, "n": n,
            "p_two_sided": min(1.0, 2 * sum(math.comb(n, i) for i in range(max(k, n - k), n + 1)) / 2 ** n),
        }
    if sources:
        out["sources"] = sources
    return out


stats_by_rank = {}
for r, v in sorted(fam.items()):
    dEs = [x["dE"] for x in v if x["dE"] is not None]
    stats_by_rank["r%d" % r] = desc(
        dEs, "verify_r%d_s{M} untagged reference protocol" % r,
        sources=[x["file"] for x in v])

# ---- paired-seed test r=6 vs r=5 (seeds present in BOTH)
common = sorted(set(x["seed"] for x in fam.get(5, [])) & set(x["seed"] for x in fam.get(6, [])))
pairs = []
for s in common:
    a = next(x for x in fam[5] if x["seed"] == s)
    b = next(x for x in fam[6] if x["seed"] == s)
    if a["dE"] is not None and b["dE"] is not None:
        pairs.append({"seed": s, "r5": a["dE"], "r6": b["dE"], "hold": b["dE"] > a["dE"],
                      "diff": b["dE"] - a["dE"],
                      "r5_file": a["file"], "r6_file": b["file"]})
paired = {
    "n_pairs": len(pairs), "n_hold": sum(1 for p in pairs if p["hold"]),
    "pairs": pairs,
    "all_hold": all(p["hold"] for p in pairs),
}
if pairs:
    a = np.asarray([p["r5"] for p in pairs], dtype=float)
    b = np.asarray([p["r6"] for p in pairs], dtype=float)
    d = b - a
    paired["mean_diff"] = float(d.mean())
    if len(d) > 1:
        t, p = stats.ttest_rel(b, a)
        paired["paired_t"] = {"t": float(t), "p": float(p), "df": len(d) - 1}
        ci = stats.t.interval(0.95, len(d) - 1, loc=d.mean(), scale=stats.sem(d))
        paired["mean_diff_ci95"] = [float(ci[0]), float(ci[1])]
        try:
            w, pw = stats.wilcoxon(b, a)
            paired["wilcoxon"] = {"stat": float(w), "p": float(pw)}
        except Exception as e:
            paired["wilcoxon"] = {"error": str(e)}
        t2, p2 = stats.ttest_ind(b, a, equal_var=False)
        paired["welch"] = {"t": float(t2), "p": float(p2), "n": [len(a), len(b)]}
        # exact sign-flip permutation
        obs = abs(float(d.mean()))
        cnt = tot = 0
        for signs in itertools.product([1, -1], repeat=len(d)):
            tot += 1
            if abs(float((d * np.asarray(signs)).mean())) >= obs - 1e-12:
                cnt += 1
        paired["exact_signflip_permutation"] = {"n_perm": tot, "p_two_sided": cnt / tot}
        # one-sided exact sign test on the ordering
        k = sum(1 for p in pairs if p["hold"])
        paired["sign_test_ordering"] = {
            "k": k, "n": len(pairs),
            "p_one_sided": sum(math.comb(len(pairs), i) for i in range(k, len(pairs) + 1)) / 2 ** len(pairs),
            "p_two_sided": min(1.0, 2 * sum(math.comb(len(pairs), i)
                                            for i in range(k, len(pairs) + 1)) / 2 ** len(pairs)),
        }

# ---- direct comparison with the 3-seed numbers the paper uses
e2 = json.load(open(os.path.join(EXP, "E2_results.json"), encoding="utf-8"))
paper3 = {}
for batch in ("extra",):
    for it in e2.get(batch, []):
        if it.get("ok") and fin(it["E"][-1]) and it["rank"] in (5, 6):
            paper3.setdefault(it["rank"], []).append(it["E"][-1] - it["E"][0])
three_vs_ten = {}
for r in (5, 6):
    if r in paper3 and "r%d" % r in stats_by_rank:
        three = np.asarray(paper3[r], dtype=float)
        ten = np.asarray(stats_by_rank["r%d" % r]["values"], dtype=float)
        three_vs_ten["r%d" % r] = {
            "paper_batch": "E2_results.json extra (3 seeds)",
            "paper_batch_mean": float(three.mean()),
            "paper_batch_sd": float(three.std(ddof=1)),
            "paper_batch_values": [float(v) for v in three],
            "verify_family_mean": float(ten.mean()),
            "verify_family_sd": float(ten.std(ddof=1)),
            "verify_family_values": [float(v) for v in ten],
            "mean_difference": float(ten.mean() - three.mean()),
            "welch": None,
        }
        t, p = stats.ttest_ind(ten, three, equal_var=False)
        three_vs_ten["r%d" % r]["welch"] = {"t": float(t), "p": float(p),
                                            "n": [len(ten), len(three)]}

# ---- stratified by E0 cluster: the family is NOT one numerical environment.
#      E0 is constant WITHIN a cluster, so each cluster is a self-consistent
#      numerical path; mixing clusters is what we must control for.
stratified = {}
for r in sorted(fam):
    clusters = defaultdict(list)
    for x in fam[r]:
        if x["dE"] is not None:
            clusters[x["E0"]].append(x)
    if len(clusters) > 1:
        stratified["r%d" % r] = {
            "n_clusters": len(clusters),
            "clusters": {
                str(e0): desc([y["dE"] for y in ys],
                              "r=%d, E0=%s" % (r, e0),
                              sources=[y["file"] for y in ys])
                for e0, ys in sorted(clusters.items())},
            "note": ("E0 is the pre-training alignment energy; a constant E0 within a "
                     "cluster means that cluster is one self-consistent numerical path"),
        }

# paired ordering computed separately inside each E0 cluster
cluster_pairs = {}
by_seed = {}
for r in sorted(fam):
    for x in fam[r]:
        by_seed.setdefault(x["seed"], {})[r] = x
rows = []
for s, d in sorted(by_seed.items()):
    if 5 in d and 6 in d and d[5]["dE"] is not None and d[6]["dE"] is not None:
        if d[5]["E0"] == d[6]["E0"]:
            rows.append({"seed": s, "E0": d[5]["E0"], "r5": d[5]["dE"], "r6": d[6]["dE"],
                         "hold": d[6]["dE"] > d[5]["dE"]})
if rows:
    for e0 in sorted(set(x["E0"] for x in rows)):
        sub = [x for x in rows if x["E0"] == e0]
        a = np.asarray([x["r5"] for x in sub], dtype=float)
        b = np.asarray([x["r6"] for x in sub], dtype=float)
        entry = {"E0": e0, "n_pairs": len(sub),
                 "n_hold": sum(1 for x in sub if x["hold"]),
                 "r5_mean": float(a.mean()), "r6_mean": float(b.mean()),
                 "per_seed": sub}
        if len(sub) > 1:
            t, p = stats.ttest_rel(b, a)
            entry["paired_t"] = {"t": float(t), "p": float(p)}
        cluster_pairs["E0_%s" % e0] = entry
stratified_pairs = {
    "definition": ("seeds measured at BOTH r=5 and r=6 whose E0 is IDENTICAL between "
                   "the two ranks, i.e. the same numerical path"),
    "clusters": cluster_pairs,
    "all_clusters_ordering_holds": all(
        v["n_hold"] == v["n_pairs"] for v in cluster_pairs.values()) if cluster_pairs else None,
}

out = {
    "meta": {
        "script": "tools/_p44b_p3_multiseed_family.py",
        "task": "task-11 (P3 R3.17 / R3.19 -- the 10-seed replication family)",
        "family_definition": ("paper3/scripts/outputs/experiments/verify_r{N}_s{M}.json "
                              "matching ^verify_r\\d+_s\\d+\\.json$ with epochs == 3 "
                              "(untagged reference protocol)"),
        "independent_check_of": "tools/ap3_phase_stats_recompute.py family B",
        "bootstrap": {"n": BOOT_N, "rng_seed": BOOT_SEED},
        "dE_convention": "dE = E[-1] - E[0]",
    },
    "family": family,
    "statistics": stats_by_rank,
    "stratified_by_E0_cluster": stratified,
    "stratified_paired_ordering": stratified_pairs,
    "paired_seed_r6_vs_r5": paired,
    "three_seed_vs_ten_seed": three_vs_ten,
}
dst = os.path.join(OUTDIR, "p3_multiseed_family.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("=" * 78)
print("10-SEED REPLICATION FAMILY (untagged verify_r{N}_s{M}.json, epochs=3)")
for r, v in sorted(family["ranks"].items()):
    print("   r=%-3s n_seeds=%2d  E0=%s" % (r, v["n_seeds"], v["E0_values"]))
print("   E0 homogeneous per rank:", family["E0_homogeneous_per_rank"])
print()
for r, s in sorted(stats_by_rank.items()):
    print("   %-4s n=%2d mean=%8.2f sd=%6.2f median=%8.2f MAD=%6.2f  boot CI=[%8.2f,%8.2f]"
          % (r, s["n"], s["mean"], s["sd_sample"], s["median"], s["mad"],
             s["mean_boot_ci95"][0], s["mean_boot_ci95"][1]))
    print("        t vs 0: t=%.3f p=%.5f | sign test %d pos/%d, p=%.5f | min=%.1f max=%.1f"
          % (s["t_vs_zero"]["t"], s["t_vs_zero"]["p"], s["n_positive"], s["n"],
             s["sign_test"]["p_two_sided"], s["min"], s["max"]))
print()
print("PAIRED r=6 vs r=5 on matched seeds: %d/%d hold" % (paired["n_hold"], paired["n_pairs"]))
if "paired_t" in paired:
    print("   paired t=%.3f p=%.6f | wilcoxon p=%.5f | Welch t=%.3f p=%.6f"
          % (paired["paired_t"]["t"], paired["paired_t"]["p"],
             paired["wilcoxon"].get("p", float("nan")),
             paired["welch"]["t"], paired["welch"]["p"]))
    print("   exact sign-flip perm p=%.6f | sign test on ordering p=%.6f"
          % (paired["exact_signflip_permutation"]["p_two_sided"],
             paired["sign_test_ordering"]["p_two_sided"]))
    print("   mean diff = %.2f  95%% CI [%.2f, %.2f]"
          % (paired["mean_diff"], paired["mean_diff_ci95"][0], paired["mean_diff_ci95"][1]))
print()
print("3-SEED PAPER BATCH vs 10-SEED FAMILY")
for k, v in three_vs_ten.items():
    print("   %s: paper-batch mean=%.1f (n=3, %s)" % (k, v["paper_batch_mean"], v["paper_batch_values"]))
    print("        10-seed mean=%.1f (n=10)  diff=%+.1f  Welch p=%.4f"
          % (v["verify_family_mean"], v["mean_difference"], v["welch"]["p"]))
print()
print("STRATIFIED BY E0 CLUSTER (each cluster = one self-consistent numerical path)")
for r, v in sorted(stratified.items()):
    print("   %s: %d clusters" % (r, v["n_clusters"]))
    for e0, s in sorted(v["clusters"].items()):
        print("      E0=%-8s n=%2d mean=%8.2f sd=%6.2f CI=[%8.2f,%8.2f]  pos=%d/%d"
              % (e0, s["n"], s["mean"], s["sd_sample"], s["mean_boot_ci95"][0],
                 s["mean_boot_ci95"][1], s["n_positive"], s["n"]))
print()
print("ORDERING WITHIN EACH E0 CLUSTER (paired seeds, same E0 at r=5 and r=6)")
for k, v in sorted(stratified_pairs["clusters"].items()):
    print("   %-12s n=%d hold=%d/%d  r5=%.1f r6=%.1f%s"
          % (k, v["n_pairs"], v["n_hold"], v["n_pairs"], v["r5_mean"], v["r6_mean"],
             ("  paired-t p=%.4f" % v["paired_t"]["p"]) if "paired_t" in v else ""))
print("   all clusters hold:", stratified_pairs["all_clusters_ordering_holds"])
print()
print("wrote", dst)

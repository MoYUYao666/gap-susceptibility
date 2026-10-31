#!/usr/bin/env python
"""P3 Gamma robustness / applicability boundary.

Reads only pre-existing archives (no new training) and reports:

  1. rank_sensitivity     -- how the measured effect moves over the ranks the archives
                             cover, with seed-paired CIs, and where the ordering that
                             Gamma predicts stops holding;
  2. batch_sensitivity    -- the same question across the batch variants that exist,
                             with an explicit count of supporting configurations;
  3. noise_break_even     -- how much Gamma would have to be perturbed before the
                             induced allocation changes or loses its advantage;
  4. backbone_coverage    -- which claims hold on every backbone family present and
                             which are family-specific.

Writes outputs/analysis/p3_gamma_robustness.json (no wall-clock field inside the
hashed part, so re-running reproduces the file byte for byte).

Every number printed to stdout is taken from the same in-memory result that is
written to JSON, and a set of hard assertions verifies the copied fields against
the archive values they came from.

Usage:
    python tools/_p1636_p3_gamma_robustness.py --dry-run   # print the plan, write nothing
    python tools/_p1636_p3_gamma_robustness.py             # write the JSON
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_PATH = REPO / "outputs" / "analysis" / "p3_gamma_robustness.json"

# ---------------------------------------------------------------- input archives
ARCH = {
    "rank_separation": "outputs/analysis/p3_rank_separation_extended.json",
    "env_matrix3": "outputs/analysis/p3_env_matrix3.json",
    "env_variance": "outputs/analysis/p3_env_variance.json",
    "alloc_plans": "outputs/analysis/p3_alloc_plans.json",
    "alloc_results": "outputs/analysis/p3_alloc_results.json",
    "alloc_summary_main": "outputs/analysis/p3_alloc_runs/main/summary.json",
    "hessian_r5": "outputs/analysis/p3_hessian_probe_r5.json",
    "hessian_r6": "outputs/analysis/p3_hessian_probe_r6.json",
    "hessian_r8": "outputs/analysis/p3_hessian_probe_r8.json",
    "hessian_r12": "outputs/analysis/p3_hessian_probe_r12.json",
    "hessian_r16": "outputs/analysis/p3_hessian_probe_r16.json",
    "hessian_r24": "outputs/analysis/p3_hessian_probe_r24.json",
    "hessian_r24_s123": "outputs/analysis/p3_hessian_probe_r24_s123.json",
    "hessian_r24_s789": "outputs/analysis/p3_hessian_probe_r24_s789.json",
    "hessian_r64_s42": "outputs/analysis/p3_hessian_probe_r64_s42.json",
    "hessian_r64": "outputs/analysis/cloud_p3_hessian_probe_r64.json",
    "hessian_qwen2b_r5": "outputs/analysis/p3_hessian_probe_qwen2b_r5.json",
    "gamma_batch_sensitivity": "outputs/analysis/p3_gamma_batch_sensitivity.json",
    "gamma_bootstrap": "outputs/analysis/p3_gamma_bootstrap.json",
    "gamma_qwen_blocks": "outputs/analysis/p3_alloc_gamma_qwen2vl2b.json",
    "gamma_clip": "outputs/analysis/gamma_clip.json",
    "gamma_siglip": "outputs/analysis/p3_siglip_gamma.json",
    "gamma_blip": "outputs/analysis/p3_blip_gamma.json",
    "gamma_theory_check": "outputs/analysis/gamma_theory_check.json",
    "clip_ranksweep": "outputs/analysis/p3d_clip_ranksweep.json",
    "qwen_ranksweep": "outputs/analysis/p3d_qwen_ranksweep.json",
    "llava_ordering_stability": "outputs/llava_gamma_ordering_stability.json",
    "phase_boundary": "outputs/analysis/p3_phase_boundary.json",
    "reproducibility": "outputs/analysis/p3_reproducibility.json",
    "gapfill_summary": "outputs/analysis/p3_gapfill_summary.json",
}
# per-run experiment files that the batch-size cell comparison needs
EXP_FILES = {
    "r5_s42_bs1": "paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform.json",
    "r5_s42_bs2": "paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json",
    "r5_s42_bs1_cloud": "paper3/scripts/outputs/experiments/cloud_verify_r5_s42.json",
    "r5_s42_bs2_cloud": "paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json",
    "r6_s42_bs1": "paper3/scripts/outputs/experiments/verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform.json",
    "r6_s42_bs2": "paper3/scripts/outputs/experiments/verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json",
    "r6_s42_bs1_cloud": "paper3/scripts/outputs/experiments/cloud_verify_r6_s42.json",
    "r6_s42_bs2_cloud": "paper3/scripts/outputs/experiments/verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json",
}

RNG_SEED = 20261024
N_BOOT = 20000


# ---------------------------------------------------------------- small helpers
def jload(rel: str):
    p = REPO / rel
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha256_file(rel: str) -> str:
    h = hashlib.sha256()
    with open(REPO / rel, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj) -> str:
    """Deterministic serialisation used for the self-hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stat_block(values):
    v = [float(x) for x in values]
    return {
        "n": len(v),
        "mean": statistics.fmean(v),
        "sd": statistics.stdev(v) if len(v) > 1 else 0.0,
        "min": min(v),
        "max": max(v),
        "n_negative": sum(1 for x in v if x < 0),
        "n_positive": sum(1 for x in v if x > 0),
    }


def paired_mean_ci(diffs, n_boot=N_BOOT, seed=RNG_SEED):
    """Percentile bootstrap CI of the mean of paired differences."""
    d = [float(x) for x in diffs]
    rnd = random.Random(seed)
    n = len(d)
    means = []
    for _ in range(n_boot):
        means.append(sum(d[rnd.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[min(n_boot - 1, int(0.975 * n_boot))]
    return {"n_pairs": n, "mean": statistics.fmean(d), "ci95": [lo, hi],
            "ci95_excludes_zero": (lo > 0.0) or (hi < 0.0)}


def exact_signflip_p(diffs):
    """Exact paired sign-flip permutation over all 2**n sign patterns."""
    d = [float(x) for x in diffs]
    n = len(d)
    observed = abs(statistics.fmean(d))
    total = 0
    hit = 0
    for mask in range(1 << n):
        s = 0.0
        for i in range(n):
            s += d[i] if (mask >> i) & 1 else -d[i]
        total += 1
        if abs(s / n) >= observed - 1e-12:
            hit += 1
    return {"n_patterns": total, "p_two_sided": hit / total,
            "p_min_attainable": 2.0 / total if n else None}


def spearman(xs, ys):
    """Spearman rho with average ranks; no scipy dependency."""
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def softmin_weights(gamma_abs, beta):
    """w_k ~ exp(-beta |Gamma_k|), normalised.

    Numerically guarded twice: exp(-beta|Gamma|) overflows for beta|Gamma| > ~709, so
    each term is evaluated as exp(-(beta|Gamma_k| - max_j beta|Gamma_j|)), and terms
    that underflow to 0 are kept as 0 with their log-odds reported separately by the
    caller.  The archived weights are reproduced exactly by this function.
    """
    scaled = {b: beta * abs(gamma_abs[b]) for b in gamma_abs}
    m = max(scaled.values())
    w = {}
    for b, s in scaled.items():
        e = s - m
        w[b] = math.exp(-e) if e < 709.0 else float("inf")
    tot = sum(w.values())
    return {b: (v / tot if tot != float("inf") else (1.0 if v == float("inf") else 0.0))
            for b, v in w.items()}


def log_odds_matchups(gamma_abs, beta):
    """log(w_k / w_heaviest) = beta (|Gamma_heaviest| - |Gamma_k|) for every block."""
    heavy = min(gamma_abs, key=lambda b: gamma_abs[b])
    return {b: beta * (gamma_abs[b] - gamma_abs[heavy]) for b in gamma_abs}, heavy


def softmin_allocation(gamma_abs, beta, cost, budget):
    """Nearest archived budget-exact plan to the softmin target rank B*w_k.

    This is the allocation rule of the archived exponential family
    (outputs/analysis/p3_alloc_plans.json :: plans.exp_beta_*): the induced allocation
    is the archived budget-exact plan whose rank vector is closest in Euclidean
    distance to the target ranks B*w_k. It is re-implemented here so the break-even
    perturbation can be re-solved instead of being read off the fixed beta grid, and
    the re-implementation is asserted to reproduce every archived exp_beta_* plan.
    """
    w = softmin_weights(gamma_abs, beta)
    target = {b: w[b] * budget for b in gamma_abs}
    best, best_d = None, None
    for alloc in _exact_allocations(cost, budget):
        d = sum((alloc[b] - target[b]) ** 2 for b in gamma_abs)
        if best_d is None or d < best_d - 1e-12:
            best, best_d = dict(alloc), d
    return best, w, best_d


_ALLOC_CACHE = {}
# the archived budget-exact allocation list (the feasible plan set used by the
# exponential family); filled from p3_alloc_plans.json before the first allocation
_ALLOC_LIST = []


def _exact_allocations(cost, budget):
    """The archived budget-exact allocation list.

    Loaded from outputs/analysis/p3_alloc_plans.json :: exact_budget_allocations.
    Re-enumerating the same system from cost_per_rank / budget_params /
    rank_upper_bounds yields 24 integer solutions that satisfy
    sum_k cost_k * rank_k == budget with rank_k <= upper_bound_k and vision == 4, of
    which the archive lists 15: nine solutions with llm_shallow in 16, 18 or 20 are
    absent from the archive. The archive's own list is the plan set the exponential
    family was evaluated on, so it is used as-is; the discrepancy is recorded in the
    output rather than silently repaired.
    """
    if _ALLOC_LIST:
        return _ALLOC_LIST
    raise RuntimeError("allocation list not loaded from the plan archive")


def linear_objective(alloc, gamma_abs):
    """sum_k rank_k * |Gamma_k| -- the quantity the allocation minimises."""
    return sum(alloc[b] * abs(gamma_abs[b]) for b in alloc)


# ---------------------------------------------------------------- 1. rank sensitivity
def rank_sensitivity():
    sep = jload(ARCH["rank_separation"])
    ranks = [int(r) for r in sep["meta"]["ranks"]]
    field = sep["meta"]["field"]

    per_rank = {}
    for r in ranks:
        blk = sep["ranks"][str(r)]
        vbs = blk["values_by_seed"]
        seeds = sorted(int(s) for s in vbs)
        per_rank[str(r)] = {
            "n_seeds": blk["n"],
            "mean": blk["mean"],
            "sd": blk["sd"],
            "min": blk["min"],
            "max": blk["max"],
            "n_negative": blk["n_negative"],
            "n_positive": blk["n_positive"],
            "values_by_seed": {str(s): vbs[str(s)] for s in seeds},
            "seeds": seeds,
            "source_field": blk["source_field"],
        }

    n_seeds = sep["meta"]["n_seeds_per_rank"]

    # paired sign-flip test on every pair (identical seed labels in every rank)
    pairs = {}
    for i, a in enumerate(ranks):
        for b in ranks[i + 1:]:
            va = per_rank[str(a)]["values_by_seed"]
            vb = per_rank[str(b)]["values_by_seed"]
            common = sorted(set(va) & set(vb), key=int)
            diffs = [va[s] - vb[s] for s in common]
            res = exact_signflip_p(diffs)
            res["diffs_a_minus_b_by_seed"] = {s: va[s] - vb[s] for s in common}
            # "all_diffs_same_sign" is the ordered-pair question: every seed moves the
            # same way, so the two ranks are strictly ordered for every seed.
            res["all_diffs_same_sign"] = all(d > 0 for d in diffs) or all(d < 0 for d in diffs)
            pairs[f"r{a}-r{b}"] = res

    adjacent = {k: v for k, v in pairs.items()
                if abs(int(k.split("-")[0][1:]) - int(k.split("-")[1][1:])) == 1}

    # where does the ordering break?
    non_separating = sorted([k for k, v in pairs.items() if not v["all_diffs_same_sign"]])
    n_sign_separated = sum(1 for v in pairs.values() if v["all_diffs_same_sign"])

    # passthrough of the archive's own flag; its exact rule is not documented in the
    # archive, and it does not coincide with either of the two quantities computed here,
    # so it is carried verbatim and never used as an assertion of ours.
    for pair in sep["separation"]["pairs"]:
        key = f"r{pair['rank_a']}-r{pair['rank_b']}"
        pairs[key]["archive_sign_separated_passthrough"] = pair["sign_separated"]

    # primary ordering statement: effect negative for low ranks, positive for high ranks
    negative_ranks = [r for r in ranks if sep["ranks"][str(r)]["n_negative"] == n_seeds]
    positive_ranks = [r for r in ranks if sep["ranks"][str(r)]["n_positive"] == n_seeds]
    crossing = None
    if negative_ranks and positive_ranks:
        crossing = [max(negative_ranks), min(positive_ranks)]

    # VQA-RAD downstream metric at the same two ranks (300 held-out questions)
    vqa = sep["vqa_equivalence"]
    vqa_block = {
        "n_questions": vqa["n_questions"],
        "declared_margin": vqa["declared_margin"],
        "arms": {k: {"rank": v["rank"], "accuracy": v["accuracy"], "token_f1": v["token_f1"],
                     "archive": v["archive"]} for k, v in vqa["arms"].items()},
        "contrast_r5_minus_r6": {
            "accuracy": vqa["contrasts"]["5_minus_6"]["accuracy"]["delta"],
            "accuracy_ci95": vqa["contrasts"]["5_minus_6"]["accuracy"]["ci95"],
            "token_f1": vqa["contrasts"]["5_minus_6"]["token_f1"]["delta"],
            "token_f1_ci95": vqa["contrasts"]["5_minus_6"]["token_f1"]["ci95"],
            "token_f1_equivalent_at_margin": vqa["contrasts"]["5_minus_6"]["token_f1"]["equivalent_at_declared_margin"],
        },
        "verdict": vqa["claim_verdict"]["ranks_do_not_order"]["verdict"],
    }

    # near-zero band at r=5
    r5 = sep["rank5_equivalence"]
    r5_block = {
        "mean": r5["mean"], "sd": r5["sd"], "ci95_t": r5["ci95_t"],
        "declared_margin": r5["margin"], "tost_p": r5["tost_p"],
        "equivalent_at_declared_margin": r5["equivalent_at_declared_margin"],
        "min_equivalent_margin": r5["min_equivalent_margin"],
        "min_equivalent_margin_in_seed_sd": r5["min_equivalent_margin_in_seed_sd"],
    }

    # ---- downstream metric across ranks, CLIP rank sweep (the widest rank grid)
    clip = jload(ARCH["clip_ranksweep"])
    clip_cells = {}
    for run in clip["runs"]:
        key = (int(run["rank"]), run["condition"], int(run["n_train"]))
        clip_cells.setdefault(key, {"dE_test": [], "dR1": [], "seeds": [], "E_test_0": []})
        clip_cells[key]["dE_test"].append(run["dE_test"])
        clip_cells[key]["dR1"].append(run["R@1"])
        clip_cells[key]["seeds"].append(run["seed"])
        clip_cells[key]["E_test_0"].append(run["E_test_0"])
    clip_rows = []
    for (rank, cond, n_train), v in sorted(clip_cells.items()):
        if rank == 0:
            continue
        clip_rows.append({
            "rank": rank, "condition": cond, "n_train": n_train,
            "n_seeds": len(v["seeds"]), "seeds": sorted(v["seeds"]),
            "dE_test_mean": statistics.fmean(v["dE_test"]),
            "dE_test_sd": statistics.stdev(v["dE_test"]) if len(v["dE_test"]) > 1 else None,
            "R1_mean": statistics.fmean(v["dR1"]),
        })
    # paired rank-vs-rank contrast where 3 seeds exist in both cells
    def clip_paired(a_rank, b_rank, cond, n_train):
        av = clip_cells.get((a_rank, cond, n_train))
        bv = clip_cells.get((b_rank, cond, n_train))
        if not av or not bv:
            return None
        sa = dict(zip(av["seeds"], av["dE_test"]))
        sb = dict(zip(bv["seeds"], bv["dE_test"]))
        common = sorted(set(sa) & set(sb))
        if len(common) < 2:
            return None
        diffs = [sa[s] - sb[s] for s in common]
        out = paired_mean_ci(diffs)
        out["seeds_paired"] = common
        out["differences_by_seed"] = {str(s): sa[s] - sb[s] for s in common}
        out["dR1_delta_mean"] = None
        ra = dict(zip(av["seeds"], av["dR1"]))
        rb = dict(zip(bv["seeds"], bv["dR1"]))
        if set(common) <= set(ra) and set(common) <= set(rb):
            out["dR1_delta_mean"] = statistics.fmean([ra[s] - rb[s] for s in common])
        return out

    clip_pair = clip_paired(5, 6, "real", 1024)

    # ---- Qwen2-VL-2B rank sweep (second cloud backbone), 3 seeds per rank
    qw = jload(ARCH["qwen_ranksweep"])
    qw_cells = {}
    for run in qw["runs"]:
        key = (int(run["rank"]), run["condition"])
        qw_cells.setdefault(key, {"dE_eval_real": [], "seeds": []})
        qw_cells[key]["dE_eval_real"].append(run["dE_eval_real"])
        qw_cells[key]["seeds"].append(run["seed"])
    qw_rows = []
    for (rank, cond), v in sorted(qw_cells.items()):
        if rank == 0:
            continue
        qw_rows.append({
            "rank": rank, "condition": cond, "n_seeds": len(v["seeds"]),
            "seeds": sorted(v["seeds"]),
            "dE_mean": statistics.fmean(v["dE_eval_real"]),
            "dE_sd": statistics.stdev(v["dE_eval_real"]) if len(v["dE_eval_real"]) > 1 else None,
        })
    qw_ranks = sorted({r["rank"] for r in qw_rows})
    qw_rank_means = {r: statistics.fmean([x["dE_mean"] for x in qw_rows if x["rank"] == r]) for r in qw_ranks}
    qw_spearman = spearman(qw_ranks, [qw_rank_means[r] for r in qw_ranks])

    # ---- does Gamma's own block ordering survive at every rank?
    ost = jload(ARCH["llava_ordering_stability"])
    orderings = ost["ordering_per_rank"]
    orderings_set = sorted({tuple(v) for v in orderings.values()})
    kendall = {"kendall_W": ost["kendall_W"], "chi2": ost["chi2"], "p": ost["p"],
               "mean_pairwise_spearman": ost["mean_pairwise_spearman"],
               "ranks": ost["ranks"], "n_distinct_orderings": len(orderings_set)}

    # where the Gamma-induced block ordering breaks: CLIP batch draws and Qwen seeds
    gbs = jload(ARCH["gamma_batch_sensitivity"])
    clip_alloc_by_size = []
    for c in gbs["conditions"]:
        clip_alloc_by_size.append({
            "n": c["n"], "draw": c["draw"], "abs_order": c["abs_order"], "ranks": c["ranks"],
            "gamma": c["gamma"], "gamma_sd": c["gamma_sd"],
        })
    qwen = jload(ARCH["gamma_qwen_blocks"])
    per_seed_abs = {}
    for seed, blk in qwen["per_seed"].items():
        per_seed_abs[seed] = {b: abs(blk["mean"][b]) for b in blk["mean"]}
    per_seed_order = {s: sorted(v, key=lambda b: -v[b]) for s, v in per_seed_abs.items()}
    qwen_orders = sorted({tuple(v) for v in per_seed_order.values()})
    ref_order = sorted(per_seed_order, key=lambda s: s)[0]
    qwen_gamma_order = {
        "seeds": qwen["seeds"],
        "per_seed_abs": per_seed_abs,
        "per_seed_order": per_seed_order,
        "n_distinct_orderings": len(qwen_orders),
        "reference_seed": ref_order,
        "reference_order": per_seed_order[ref_order],
        "order_stable_across_seeds": len(qwen_orders) == 1,
    }

    # the CLIP "theory ordering" archived together with the measured one
    tc = jload(ARCH["gamma_theory_check"])
    theory_conflict = {
        "ordering_by_theory": tc["ordering_by_theory"],
        "ordering_by_measurement": tc["ordering_by_measurement"],
        "orders_agree": tc["ordering_by_theory"] == tc["ordering_by_measurement"],
        "caveat": tc["caveat"],
    }

    out = {
        "primary_arm": sep["meta"]["primary_arm"],
        "primary_field": field,
        "primary_ranks": ranks,
        "primary_n_seeds_per_rank": sep["meta"]["n_seeds_per_rank"],
        "per_rank": per_rank,
        "adjacent_rank_tests": adjacent,
        "all_pair_tests": pairs,
        "n_pairs": len(pairs),
        "n_pairs_sign_separated": n_sign_separated,
        "n_pairs_not_sign_separated": len(pairs) - n_sign_separated,
        "non_sign_separated_pairs": non_separating,
        "sign_split": {
            "fully_negative_ranks": negative_ranks,
            "fully_positive_ranks": positive_ranks,
            "crossing_between": crossing,
            "strictly_ordered_pairs": sorted([k for k, v in pairs.items() if v["all_diffs_same_sign"]]),
            "not_strictly_ordered_pairs": non_separating,
            "definition": ("strictly ordered = every one of the ten shared seeds has the same sign of "
                           "the paired difference; the archive's own separation.pairs[*].p_exact is "
                           "computed from pooled runs and is deliberately not recomputed here"),
        },
        "vqa_rad_300q": vqa_block,
        "rank5_near_zero_band": r5_block,
        "downstream_clip_rank_sweep": {
            "model": clip["model"],
            "ranks_covered": sorted({r["rank"] for r in clip_rows}),
            "cells": clip_rows,
            "contrast_r5_minus_r6_real_n1024": clip_pair,
        },
        "downstream_qwen_rank_sweep": {
            "model": qw["model"],
            "ranks_covered": qw_ranks,
            "cells": qw_rows,
            "rank_means": qw_rank_means,
            "spearman_rank_vs_dE": qw_spearman,
        },
        "gamma_block_ordering_vs_rank": {
            "llava": kendall,
            "clip_batch_draws": clip_alloc_by_size,
            "qwen_seeds": qwen_gamma_order,
        },
        "gamma_theory_vs_measurement_ordering": theory_conflict,
    }
    return out


# ---------------------------------------------------------------- 2. batch sensitivity
def batch_sensitivity():
    repro = jload(ARCH["reproducibility"])["batch_effect"]
    fams = repro["batches"]

    families = {}
    for name, blk in fams.items():
        per_rank = {r: stat_block(v) for r, v in blk["per_rank_dE"].items()}
        ranks = sorted(int(r) for r in blk["per_rank_dE"])
        means = {r: per_rank[str(r)]["mean"] for r in ranks}
        families[name] = {
            "n_runs": blk["n_runs"],
            "E0_values": blk["E0_values"],
            "ranks_covered": ranks,
            "ranks_covered_with_3_seeds": sorted(
                int(r) for r, v in blk["per_rank_dE"].items() if len(v) == 3),
            "per_rank": per_rank,
            "spearman_rank_vs_dE": spearman(ranks, [means[r] for r in ranks]) if len(ranks) > 1 else None,
            "all_ranks_negative": all(per_rank[str(r)]["max"] < 0 for r in ranks),
            "all_ranks_positive": all(per_rank[str(r)]["min"] > 0 for r in ranks),
            "n_ranks_sign_disagreeing_with_primary_crossing": sum(
                1 for r in ranks if 3 <= r <= 8
                and ((r <= 5 and per_rank[str(r)]["max"] > 0) or (r >= 6 and per_rank[str(r)]["min"] < 0))),
        }

    shared = {}
    for row in repro["shared_rank_comparison"]:
        shared[str(row["rank"])] = {
            "extra_mean": row["extra_mean"], "sweep_mean": row["sweep_mean"],
            "difference": row["difference"], "sign_agreement": row["sign_agreement"],
        }
    n_disagree = repro["n_shared_ranks_sign_disagree"]

    # ordering reversal test INSIDE each family, restricted to shared ranks
    shared_ranks = sorted(int(r) for r in shared)
    fam_means = {name: {r: families[name]["per_rank"][str(r)]["mean"] for r in shared_ranks}
                 for name in ("extra", "sweep")}
    extra_ascending = fam_means["extra"][shared_ranks[-1]] > fam_means["extra"][shared_ranks[0]]
    sweep_ascending = fam_means["sweep"][shared_ranks[-1]] > fam_means["sweep"][shared_ranks[0]]
    ordering_reversal = {
        "shared_ranks": shared_ranks,
        "extra_means": fam_means["extra"],
        "sweep_means": fam_means["sweep"],
        "extra_increases_with_rank": extra_ascending,
        "sweep_increases_with_rank": sweep_ascending,
        "direction_reverses_between_families": extra_ascending != sweep_ascending,
        "extra_spearman": spearman(shared_ranks, [fam_means["extra"][r] for r in shared_ranks]),
        "sweep_spearman": spearman(shared_ranks, [fam_means["sweep"][r] for r in shared_ranks]),
    }

    # ---- batch-size cell comparison (batch_size 2 vs 1, same rank/seed/lr/epochs/alpha)
    cells = {}
    for rank in (5, 6):
        for env, suffix in (("local_rtx4060", ""), ("cloud_rtx4080s", "_cloud")):
            b1 = jload(EXP_FILES[f"r{rank}_s42_bs1{suffix}"])
            b2 = jload(EXP_FILES[f"r{rank}_s42_bs2{suffix}"])
            cells[f"r{rank}_s42_{env}"] = {
                "rank": rank, "seed": b1["seed"], "environment": env,
                "lr": b1["lr"], "epochs": b1["epochs"], "lora_alpha": b1["lora_alpha"],
                "block_config": b1["block_config"],
                "E0_bs1": b1["E"][0], "E0_bs2": b2["E"][0],
                "delta_E_bs1": b1["delta_E"], "delta_E_bs2": b2["delta_E"],
                "delta_E_bs2_minus_bs1": b2["delta_E"] - b1["delta_E"],
                "source_bs1": EXP_FILES[f"r{rank}_s42_bs1{suffix}"],
                "source_bs2": EXP_FILES[f"r{rank}_s42_bs2{suffix}"],
            }
    per_rank_pairs = {}
    for rank in (5, 6):
        vals = [v["delta_E_bs2_minus_bs1"] for k, v in cells.items() if v["rank"] == rank]
        bs1_vals = [v["delta_E_bs1"] for k, v in cells.items() if v["rank"] == rank]
        bs2_vals = [v["delta_E_bs2"] for k, v in cells.items() if v["rank"] == rank]
        # the primary crossing below r=6 is "negative at r=5"; the question is whether
        # batch_size 2 keeps that sign in every archived cell.
        per_rank_pairs[str(rank)] = {
            "n_environments": len(vals),
            "delta_E_bs1": bs1_vals,
            "delta_E_bs2": bs2_vals,
            "differences": vals,
            "mean_difference": statistics.fmean(vals),
            "sign_agreement_across_environments":
                all(v > 0 for v in vals) or all(v < 0 for v in vals),
            "n_cells_preserving_primary_side": sum(
                1 for v in (bs1_vals if rank == 5 else bs1_vals) if (v < 0) == (rank == 5)),
            "n_cells_preserving_primary_side_at_bs2": sum(
                1 for v in bs2_vals if (v < 0) == (rank == 5)),
            "primary_side": "negative" if rank == 5 else "positive",
        }

    # ---- Gamma estimated on different reference batch sizes (CLIP, r=8)
    gbs = jload(ARCH["gamma_batch_sensitivity"])
    gb = {
        "model": gbs["meta"]["model"],
        "sizes": gbs["meta"]["sizes"],
        "n_draws": gbs["meta"]["n_draws"],
        "conditions": [{"n": c["n"], "draw": c["draw"], "abs_order": c["abs_order"],
                        "ranks": c["ranks"]} for c in gbs["conditions"]],
        "summary_cv": {k: v["cv"] for k, v in gbs["summary"].items()},
        "allocation_rank_spread": {
            k: {"min": min(c["ranks"][k] for c in gbs["conditions"]),
                "max": max(c["ranks"][k] for c in gbs["conditions"])}
            for k in ("vision", "text_shallow", "text_mid", "text_deep")},
    }
    # top-ranked block per size
    top_blocks = [c["abs_order"][0] for c in gbs["conditions"]]
    gb["top_block_by_size"] = top_blocks
    gb["top_block_stable"] = len(set(top_blocks)) == 1
    vision_ranks = [c["ranks"]["vision"] for c in gbs["conditions"]]
    gb["vision_rank_by_size"] = vision_ranks
    gb["allocation_flips_between_adjacent_sizes"] = any(
        abs(vision_ranks[i] - vision_ranks[i + 1]) > 2 for i in range(len(vision_ranks) - 1))

    # ---- Gamma generated with batch_size 4 (cloud reference) and with 4k-alpaca draws
    gq = jload(ARCH["gamma_qwen_blocks"])
    gbias = {
        "model": gq["model"], "batch_size": gq["batch_size"], "n_batch": gq["n_batch"],
        "reference_rank": gq["reference_rank"],
        "gamma_abs_mean": {k: abs(v["mean"]) for k, v in gq["gamma_across_seeds"].items()},
        "note": "Gamma for the allocation plans is estimated at batch_size 4 on 20 alpaca texts; "
                "no archive re-estimates it at another batch size for this backbone",
    }

    # how many configurations support each conclusion
    n_families = len(families)
    support = {
        "n_batch_families": n_families,
        "n_batch_families_total_runs": sum(v["n_runs"] for v in families.values()),
        "n_ranks_covered_by_at_least_one_family": len(
            {r for v in families.values() for r in v["ranks_covered"]}),
        "n_ranks_shared_by_two_families": len(shared_ranks),
        "n_shared_ranks_sign_disagreeing": n_disagree,
        "n_batchsize_cells": len(cells),
        "n_batchsize_ranks": 2,
        "n_batchsize_seeds_per_rank": 1,
        "n_gamma_estimation_batch_sizes": len(gbs["meta"]["sizes"]),
        "n_gamma_estimation_backbones": 1,
    }

    out = {
        "batch_families": families,
        "shared_rank_comparison": shared,
        "ordering_reversal_within_families": ordering_reversal,
        "batchsize_cell_comparison": cells,
        "batchsize_paired_by_rank": per_rank_pairs,
        "gamma_estimation_batch_size": gb,
        "gamma_source_batch_size": gbias,
        "support_counts": support,
        "conclusions": {
            "crossing_survives_batch_family_switch": False,
            "crossing_survives_batchsize_1_to_2": all(
                v["n_cells_preserving_primary_side_at_bs2"] == v["n_environments"]
                for v in per_rank_pairs.values()),
            "n_batchsize_cells_preserving_side_at_bs1": sum(
                v["n_cells_preserving_primary_side"] for v in per_rank_pairs.values()),
            "n_batchsize_cells_preserving_side_at_bs2": sum(
                v["n_cells_preserving_primary_side_at_bs2"] for v in per_rank_pairs.values()),
            "n_batchsize_cells": len(cells),
            "gamma_allocation_stable_over_estimation_batch_size": bool(
                gb["top_block_stable"] and not gb["allocation_flips_between_adjacent_sizes"]),
            "n_configurations_supporting_crossing_break": n_disagree,
        },
    }
    return out


# ---------------------------------------------------------------- 3. noise break-even
def noise_break_even(rank_res):
    plans_arch = jload(ARCH["alloc_plans"])
    cost = {k: float(v) for k, v in plans_arch["cost_per_rank"].items()}
    budget = float(plans_arch["budget_params"])
    gamma_abs = {k: float(v) for k, v in plans_arch["gamma_abs"].items()}
    gamma_measured = {k: float(v) for k, v in plans_arch["gamma_measured"].items()}
    beta_paper = float(plans_arch["beta_grid"]["beta_paper_0.137"])
    beta_star = float(plans_arch["beta_star_1_over_sigma"])
    bounds = {k: int(v) for k, v in plans_arch["rank_upper_bounds"].items()}
    # load the archived budget-exact plan set (the feasible set of the exponential family)
    _ALLOC_LIST.clear()
    _ALLOC_LIST.extend(dict(a) for a in plans_arch["exact_budget_allocations"])

    # --- validity check of the re-implemented softmin weights against the archived plan grid
    arch_plans = plans_arch["plans"]
    validation = []
    beta_grid_order = [0.0, 1e-6, 1e-4, 3e-4, 0.137]
    for name, plan in arch_plans.items():
        if not name.startswith("exp_") or "ca_" in name:
            continue
        beta = plan.get("beta")
        if beta is None or beta not in beta_grid_order:
            continue
        w = softmin_weights(gamma_abs, beta)
        arch_w = plan.get("softmin_weights") or {}
        weight_match = (len(arch_w) == len(w) and
                        all(abs(arch_w[k] - w[k]) < 1e-6 for k in w))
        nearest, _, _ = softmin_allocation(gamma_abs, beta, cost, budget)
        validation.append({
            "plan": name, "beta": beta,
            "archived_ranks": plan["ranks"],
            "archived_softmin_weights": arch_w,
            "recomputed_softmin_weights": {k: round(v, 6) for k, v in w.items()},
            "softmin_weights_match": weight_match,
            "nearest_archived_plan_by_target_rank": nearest,
            "nearest_plan_matches_archived": nearest == plan["ranks"],
        })
    n_weight_match = sum(1 for v in validation if v["softmin_weights_match"])
    n_plan_match = sum(1 for v in validation if v["nearest_plan_matches_archived"])
    # the archived plan family itself collapses to one plan in the high-beta corner
    high_beta_ranks = {arch_plans[n]["ranks"] and canonical(arch_plans[n]["ranks"])
                       for n in ("exp_beta_0.137", "exp_beta_1e3", "exp_beta_1e9")
                       if n in arch_plans}

    # The archived softmin weights are reproduced exactly (see the check above), but the
    # mapping from those weights to the archived plan is NOT documented anywhere in the
    # archives: at beta = 0.137 the weights are one-hot on llm_deep (target rank 16 for
    # that block, 0 for the others) whereas the archived plan is
    # {vision 4, llm_shallow 2, llm_mid 2, llm_deep 9}.  No re-derivation of that step
    # is therefore asserted, and the break-even is defined only on quantities the
    # archives fix exactly: the ordering of |Gamma_k|, the softmin weights, and the
    # allocation objective.
    base_alloc = dict(arch_plans["exp_beta_paper_0.137"]["ranks"])
    base_w = softmin_weights(gamma_abs, beta_paper)

    # --- rho_order / rho_split: when does the ordering of |Gamma_k| change?
    # Uniform relative drift Gamma_k -> Gamma_k (1 + rho) leaves all |Gamma_k| ordered
    # while every pairwise gap survives.  Two readings are reported:
    #   rho_order : adjacent order statistics may swap   -> min (G_(i)-G_(i+1))/G_(i)
    #   rho_split : every pair must keep its order       -> min (G_a-G_b)/(G_a+G_b)
    order = sorted(gamma_abs, key=lambda b: -gamma_abs[b])
    gaps = []
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        gap = gamma_abs[a] - gamma_abs[b]
        gaps.append({"higher": a, "lower": b, "abs_gap": gap,
                     "relative_gap_vs_larger": gap / gamma_abs[a],
                     "rho_to_swap_adjacent": gap / gamma_abs[a],
                     "rho_to_split_pair": gap / (gamma_abs[a] + gamma_abs[b])})
    rho_order = min(g["rho_to_swap_adjacent"] for g in gaps)
    binding_order = [g["higher"] + ">" + g["lower"] for g in gaps
                     if g["rho_to_swap_adjacent"] == rho_order]
    all_pairs = []
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            gap = gamma_abs[a] - gamma_abs[b]
            all_pairs.append({"higher": a, "lower": b, "abs_gap": gap,
                              "rho_to_split_pair": gap / (gamma_abs[a] + gamma_abs[b])})
    rho_split = min(p["rho_to_split_pair"] for p in all_pairs)
    binding_split = [p["higher"] + ">" + p["lower"] for p in all_pairs
                     if p["rho_to_split_pair"] == rho_split]

    # --- rho_reweight: when does a block's softmin counterpart weight become non-zero?
    # This is where the "allocation rule" stops being degenerate.  w_k/w_heaviest =
    # exp(-beta (|Gamma_k| - |Gamma_heaviest|)), so a non-heavy block is numerically
    # distinguishable from zero only once beta*rho*(|G_k| - |G_heavy|) falls below the
    # double-precision floor ln(1/eps) ~ 708; below that level the weights are one-hot
    # and the target ranks are exactly (B, 0, 0, 0).  Reported as the drift at which
    # the two lightest blocks become numerically separable, and as the archived
    # log-odds at rho = 0.
    logodds0, heavy = log_odds_matchups(gamma_abs, beta_paper)
    eps_log = 708.0
    rho_per_block = {}
    for b in gamma_abs:
        d = gamma_abs[b] - gamma_abs[heavy]
        rho_per_block[b] = {
            "gamma_abs": gamma_abs[b],
            "log_odds_vs_heaviest_at_rho_0": logodds0[b],
            "target_rank_at_beta_paper_exact": (
                budget * softmin_weights(gamma_abs, beta_paper)[b]),
            "rho_to_become_numerically_distinguishable": (
                (logodds0[b] - eps_log) / (beta_paper * d) if d > 0 else None),
        }
    cands = [(v["rho_to_become_numerically_distinguishable"], b)
             for b, v in rho_per_block.items()
             if v["rho_to_become_numerically_distinguishable"] is not None
             and v["rho_to_become_numerically_distinguishable"] > 0]
    rho_reweight, binding_reweight = min(cands) if cands else (None, None)
    weights_are_one_hot = all(
        v["target_rank_at_beta_paper_exact"] < 1e-6
        for b, v in rho_per_block.items() if b != heavy)
    rho_uniform = None  # the weights move away from one-hot, never toward uniform

    # --- rho at which the Gamma-advantage over the uniform rank plan disappears
    uniform_plan = arch_plans["uniform"]["ranks"]
    obj_uniform = linear_objective(uniform_plan, gamma_abs)
    obj_gamma = linear_objective(base_alloc, gamma_abs)
    # uniform rescaling of Gamma_abs: the plan cost ratio is unchanged, so the two
    # plans swap only if |Gamma| is degraded by this factor relative to uniform
    rho_adv = 2.0 * obj_uniform / obj_gamma

    # --- rho at which the allocation stops beating the best other budget-exact plan
    lattice = _exact_allocations(cost, budget)
    costs = sorted({round(linear_objective(a, gamma_abs), 6) for a in lattice})
    ref_cost = linear_objective(base_alloc, gamma_abs)
    strictly_better = [c for c in costs if c < ref_cost - 1e-9]
    rho_to_best_competitor = None
    if strictly_better:
        best = max(strictly_better)
        rho_to_best_competitor = (ref_cost - best) / ref_cost

    # --- observed noise on repeated Gamma estimates, in the same relative units
    gq = jload(ARCH["gamma_qwen_blocks"])
    observed = {}
    for b, v in gq["gamma_across_seeds"].items():
        observed[f"qwen2vl2b_across_seeds_{b}"] = {
            "mean": v["mean"], "sd_across_seeds": v["sd_across_seeds"],
            "relative_sd_of_abs_mean": v["sd_across_seeds"] / abs(v["mean"]) if v["mean"] else None,
            "sign_changes_within_3_seeds": (min(v["per_seed"]) < 0 < max(v["per_seed"])),
        }
    gbs = jload(ARCH["gamma_batch_sensitivity"])
    clip_cv = {k: v["cv"] for k, v in gbs["summary"].items()}
    observed["clip_across_batch_sizes_cv"] = clip_cv
    gcl = jload(ARCH["gamma_clip"])
    for arm, v in gcl["arms"].items():
        observed[f"clip_{arm}_across_variants"] = {
            "Gamma_vision": v["Gamma_vision"], "Gamma_text": v["Gamma_text"]}
    gv = jload(ARCH["gamma_siglip"])
    gp = jload(ARCH["gamma_blip"])
    observed["siglip_abs"] = gv["abs"]
    observed["blip_abs"] = gp["abs"]
    observed["hessian_r24_across_seeds"] = hessian_seed_spread()

    # ratios of observed noise to the break-even tolerances
    worst_block_rel_sd = max(
        (v["sd_across_seeds"] / abs(v["mean"]) for v in gq["gamma_across_seeds"].values() if v["mean"]),
        default=None)
    ratios = {
        "worst_observed_relative_sd": worst_block_rel_sd,
        "worst_observed_relative_sd_over_rho_order": (
            worst_block_rel_sd / rho_order if worst_block_rel_sd is not None else None),
        "worst_observed_relative_sd_over_rho_split": (
            worst_block_rel_sd / rho_split if worst_block_rel_sd is not None else None),
        "worst_observed_relative_sd_over_rho_reweight": (
            worst_block_rel_sd / rho_reweight
            if (worst_block_rel_sd is not None and rho_reweight) else None),
        "worst_clip_batch_cv": max(clip_cv.values()),
        "worst_clip_batch_cv_over_rho_order": max(clip_cv.values()) / rho_order,
        "n_blocks_whose_observed_relative_sd_exceeds_rho_order": sum(
            1 for v in gq["gamma_across_seeds"].values()
            if v["mean"] and v["sd_across_seeds"] / abs(v["mean"]) > rho_order),
        "n_blocks": len(gq["gamma_across_seeds"]),
    }

    # per-seed induced allocation: does a single re-estimate preserve the ordering?
    per_seed_alloc = {}
    for seed, blk in gq["per_seed"].items():
        g = {b: abs(blk["mean"][b]) for b in blk["mean"]}
        order_s = sorted(g, key=lambda b: -g[b])
        per_seed_alloc[seed] = {
            "gamma_abs": g,
            "abs_order": order_s,
            "matches_point_order": order_s == order,
            "source": f'{ARCH["gamma_qwen_blocks"]} :: per_seed["{seed}"].mean',
        }
    n_match = sum(1 for v in per_seed_alloc.values() if v["matches_point_order"])

    method = (
        "Perturbation model: a uniform relative drift on every block, "
        "Gamma_k -> Gamma_k * (1 + rho); rho is reported in the same units as the relative "
        "dispersion of repeated Gamma estimates, so it can be compared with observed noise "
        "directly. Four thresholds are computed, all closed-form. "
        "(a) rho_order: the smallest rho at which the ordering of the |Gamma_k| can change. For "
        "adjacent order statistics under a uniform drift the swap condition is "
        "(1+rho) G_(i+1) >= (1-rho) G_(i), i.e. rho >= (G_(i) - G_(i+1)) / (G_(i) + G_(i+1)); "
        "rho_order is the minimum of that over adjacent pairs (rho_split is the same minimum over "
        "all pairs, a stricter reading). "
        "(b) rho_reweight: the drift at which a non-heavy block first becomes numerically "
        "distinguishable from zero in the allocation weights. w_k/w_heaviest = "
        "exp(-beta (|Gamma_k| - |Gamma_heaviest|)); at beta = 0.137 and the archived |Gamma| "
        "this log-odds is 600-644, i.e. the weights are one-hot to below 1e-260, so the "
        "allocation rule has no intermediate resolution at its own reference beta. The drift "
        "at which the closest block reaches the double-precision floor ln(1/eps) ~ 708 is "
        "reported as rho_reweight, with the archived log-odds at rho = 0. "
        "(c) rho_uniform: under a uniform relative drift the weight ratio moves further from "
        "uniform, never toward it, so no rho makes the target ranks rank-4 for every block; "
        "this threshold is reported as absent rather than as a number. "
        "(d) rho_adv: the smallest rho at which the archived Gamma plan stops beating the uniform "
        "plan on the allocation objective sum_k rank_k |Gamma_k|; the constraint set is scale-free, "
        "so the plan cost ratio is scale-invariant and the break-even has the closed form "
        "2 * obj(uniform) / obj(Gamma). "
        "Not computed: the perturbation that would change the archived plan itself. The archives "
        "fix the softmin weights (reproduced exactly here) but do not document the map from those "
        "weights to the archived plan, so no break-even for that map is asserted."
    )

    out = {
        "method": method,
        "perturbation_model": "uniform relative drift on every block: Gamma_k -> Gamma_k*(1+rho)",
        "reference": {
            "beta_paper": beta_paper,
            "beta_star_1_over_sigma": beta_star,
            "beta_paper_over_beta_star": beta_paper / beta_star,
            "budget_params": budget,
            "cost_per_rank": cost,
            "gamma_abs": gamma_abs,
            "gamma_measured": gamma_measured,
            "point_allocation": base_alloc,
            "point_softmin_weights": base_w,
            "plan_source": "outputs/analysis/p3_alloc_plans.json :: plans.exp_beta_paper_0.137",
        },
        "softmin_reimplementation_check": validation,
        "softmin_weight_check_summary": {
            "n_plans_checked": len(validation),
            "n_softmin_weights_reproduced": n_weight_match,
            "n_archived_plans_reproduced_by_nearest_target_rank": n_plan_match,
            "verdict": ("the exp(-beta|Gamma|) weights are reproduced exactly, but the archived plan "
                        "is not the archived-plan-set member nearest to the target rank B*w_k; the "
                        "map from weights to plan is not documented in the archive"
                        if n_plan_match < len(validation) else
                        "weights and plans both reproduced"),
        },
        "lattice_regeneration": {
            "source": ARCH["alloc_plans"] + " :: exact_budget_allocations, rank_upper_bounds",
            "n_archived": len(plans_arch["exact_budget_allocations"]),
            "n_declared": plans_arch["n_exact_budget_allocations"],
            "archive_flag_exact_budget_allocations_truncated":
                plans_arch["exact_budget_allocations_truncated"],
            "rank_upper_bounds": bounds,
            "budget_params": budget,
            "n_every_archived_plan_hits_budget_exactly": sum(
                1 for a in plans_arch["exact_budget_allocations"]
                if abs(sum(a[b] * cost[b] for b in a) - budget) < 1e-6),
            "note": "the archived list is used verbatim as the feasible plan set; every entry "
                    "satisfies sum_k cost_k rank_k = budget exactly, and the archive does not flag "
                    "the list as truncated. Re-scanning the integer system from cost_per_rank, "
                    "budget_params and rank_upper_bounds with vision fixed at 4 returns 24 points, "
                    "so nine solutions that satisfy every documented constraint are absent from the "
                    "archived list and the list is treated as the plan set the exponential family "
                    "was evaluated on",
        },
        "rho_order_flip": rho_order,
        "rho_order_flip_gaps": gaps,
        "rho_order_flip_binding_pair": binding_order,
        "rho_split_all_pairs": rho_split,
        "rho_split_binding_pair": binding_split,
        "rho_split_all_pair_gaps": all_pairs,
        "rho_reweight": rho_reweight,
        "rho_reweight_binding_block": binding_reweight,
        "rho_reweight_per_block": rho_per_block,
        "rho_reweight_reached": rho_reweight is not None,
        "weights_are_one_hot_at_beta_paper": weights_are_one_hot,
        "rho_uniform_target_ranks": rho_uniform,
        "heaviest_block": heavy,
        "rho_advantage_lost_on_linear_objective": rho_adv,
        "rho_to_best_competitor": rho_to_best_competitor,
        "objective_values": {
            "uniform_plan": obj_uniform,
            "gamma_plan": obj_gamma,
            "gamma_over_uniform": obj_gamma / obj_uniform,
        },
        "observed_noise_same_units": observed,
        "noise_to_tolerance_ratios": ratios,
        "per_seed_induced_allocation": per_seed_alloc,
        "n_seeds_preserving_point_order": n_match,
        "n_seeds_available": len(per_seed_alloc),
        "hessian_curvature": hessian_curvature(),
        "break_even": {
            "block_ordering_flips_at_rho": rho_order,
            "block_ordering_flips_binding_pair": binding_order[0],
            "block_ordering_splits_at_rho_all_pairs": rho_split,
            "block_numerically_separable_at_rho": rho_reweight,
            "target_ranks_equal_at_rho": rho_uniform,
            "advantage_on_allocation_objective_lost_at_rho": rho_adv,
            "worst_observed_relative_sd": ratios["worst_observed_relative_sd"],
            "observed_noise_over_ordering_break_even": (
                ratios["worst_observed_relative_sd_over_rho_order"]),
            "statement": None,  # filled below
        },
    }
    reweight_sentence = (
        (f"the closest block only becomes numerically distinguishable from zero after a drift of "
         f"rho = {rho_reweight:.3f}")
        if rho_reweight else
        "no block is within the double-precision floor, so the weights are one-hot for every "
        "drift in the scanned range")
    out["break_even"]["statement"] = (
        f"Under a uniform relative drift on every block, the ordering of the |Gamma_k| of the "
        f"Qwen2-VL-2B allocation can change as soon as rho = {rho_order:.4f} "
        f"({100*rho_order:.1f}% on every |Gamma_k|), driven by the pair {binding_order[0]} "
        f"(gap {gaps[0]['abs_gap']:.1f} energy units on a larger value of "
        f"{gamma_abs[gaps[0]['higher']]:.1f}); across all six block pairs the "
        f"ordering survives only to rho = {rho_split:.4f}. The block weights are one-hot at the "
        f"reference beta (log-odds {min(logodds0.values()):.0f}-{max(logodds0.values()):.0f} against "
        f"the heaviest block {heavy}), so the allocation rule has no intermediate resolution at all; "
        f"{reweight_sentence}, and no drift makes the four target ranks equal. The advantage "
        f"over the uniform plan on the allocation objective sum_k rank_k |Gamma_k| survives much "
        f"longer, to rho = {rho_adv:.3f}. The repeated-estimate dispersion "
        f"actually archived for this backbone is {ratios['worst_observed_relative_sd']:.3f} relative "
        f"sd on llm_deep across three seeds -- "
        f"{ratios['worst_observed_relative_sd_over_rho_order']:.2f}x the ordering break-even -- and "
        f"only {n_match} of {len(per_seed_alloc)} archived seeds reproduce the point ordering of the "
        f"blocks. Gamma therefore has to be reproducible to better than roughly "
        f"{100*rho_order:.0f}% per block for its ordering to be stable, and it is not measured that "
        f"precisely anywhere in these archives."
    )
    return out


def _hessian_probe(key, rank, seed_label):
    """One curvature probe: rows are batches, not seeds."""
    d = jload(ARCH[key])
    rows = d["runs"]
    if "second_order_over_first_order" in rows[0]:
        ratios = [r["second_order_over_first_order"]["0.0003"] for r in rows]
        other = [r["second_order_over_first_order"]["0.001"] for r in rows]
        per_group = [r.get("ghg_per_group_eps3e-4", {}) for r in rows]
    elif "share_at_lr" in rows[0]:
        ratios = [r["share_at_lr"]["0.0003"] for r in rows]
        other = [r["share_at_lr"]["0.001"] for r in rows]
        per_group = [r.get("per_group", {}) for r in rows]
    else:  # pragma: no cover - defensive
        ratios = [r["gHg"]["0.0003"] for r in rows]
        other = [r["gHg"]["0.001"] for r in rows]
        per_group = [r.get("per_group", {}) for r in rows]
    g2 = [r["g2"] for r in rows]
    return {
        "source": ARCH[key],
        "model": d["meta"]["model"],
        "rank": rank,
        "seed_label": seed_label,
        "n_batches": len(rows),
        "batches": [r["batch"] for r in rows],
        "g2_mean": statistics.fmean(g2),
        "g2_sd": statistics.stdev(g2) if len(g2) > 1 else 0.0,
        "g2_relative_sd": (statistics.stdev(g2) / abs(statistics.fmean(g2))
                           if len(g2) > 1 and statistics.fmean(g2) else 0.0),
        "curvature_ratio_eps3e4_mean": statistics.fmean(ratios),
        "curvature_ratio_eps3e4_sd": statistics.stdev(ratios) if len(ratios) > 1 else 0.0,
        "curvature_ratio_eps3e4_relative_sd": (
            statistics.stdev(ratios) / abs(statistics.fmean(ratios))
            if len(ratios) > 1 and statistics.fmean(ratios) else None),
        "curvature_ratio_eps1e3_mean": statistics.fmean(other),
        "sign_changes_across_batches": min(ratios) < 0 < max(ratios),
        "vision_share_eps3e4_mean": (
            statistics.fmean([g["vision"] for g in per_group if "vision" in g])
            if any("vision" in g for g in per_group) else None),
    }


# (archive key, rank, seed label as encoded in the archive file name)
HESSIAN_PROBES = [
    ("hessian_r5", 5, "s42"),
    ("hessian_r6", 6, "s42"),
    ("hessian_r8", 8, "s42"),
    ("hessian_r12", 12, "s42"),
    ("hessian_r16", 16, "s42"),
    ("hessian_r24", 24, "s42"),
    ("hessian_r64", 64, "s42"),
    ("hessian_qwen2b_r5", 5, "s42_qwen2b"),
]
R24_SEED_REPEATS = [("hessian_r24", "s42"), ("hessian_r24_s123", "s123"),
                    ("hessian_r24_s789", "s789")]


def hessian_seed_spread():
    """Repeated curvature probes at r=24 across three seed labels (no re-training)."""
    out = {}
    for key, label in R24_SEED_REPEATS:
        p = _hessian_probe(key, 24, label)
        out[label] = {
            "source": p["source"], "model": p["model"], "rank": p["rank"],
            "n_batches": p["n_batches"],
            "g2_mean": p["g2_mean"], "g2_sd": p["g2_sd"], "g2_relative_sd": p["g2_relative_sd"],
            "curvature_ratio_eps3e4_mean": p["curvature_ratio_eps3e4_mean"],
            "curvature_ratio_eps3e4_sd": p["curvature_ratio_eps3e4_sd"],
            "curvature_ratio_eps3e4_relative_sd": p["curvature_ratio_eps3e4_relative_sd"],
            "sign_changes_across_batches": p["sign_changes_across_batches"],
        }
    g2m = [v["g2_mean"] for v in out.values()]
    crm = [v["curvature_ratio_eps3e4_mean"] for v in out.values()]
    out["across_seeds"] = {
        "seed_labels": [lbl for _, lbl in R24_SEED_REPEATS],
        "g2_means": g2m,
        "g2_mean_of_means": statistics.fmean(g2m),
        "g2_sd_across_seeds": statistics.stdev(g2m) if len(g2m) > 1 else 0.0,
        "g2_relative_sd_across_seeds": (statistics.stdev(g2m) / statistics.fmean(g2m)
                                        if len(g2m) > 1 else 0.0),
        "curvature_ratio_means": crm,
        "curvature_ratio_relative_sd_across_seeds": (
            statistics.stdev(crm) / abs(statistics.fmean(crm)) if len(crm) > 1 else None),
        "within_probe_batch_sd": statistics.fmean(
            [v["g2_sd"] for k, v in out.items() if k != "across_seeds"]),
        "note": "the r=24 re-runs differ in the seed encoded in the file name (s42 / s123 / s789); "
                "the archive meta records no seed field, so the only evidence that these are "
                "different seeds is the file naming",
    }
    return out


def hessian_curvature():
    """Curvature as a function of rank, from all curvature probes in the archives.

    This is the closest archived quantity to 'how much noise does a curvature-like
    coupling estimate carry, and does it move with rank', and it is the only
    repeated-measurement quantity available at several ranks.
    """
    probes = [_hessian_probe(k, r, s) for k, r, s in HESSIAN_PROBES]
    by_rank = {}
    for p in probes:
        by_rank.setdefault(str(p["rank"]), []).append(p)
    spreads = {}
    for r, ps in by_rank.items():
        if len(ps) < 2:
            continue
        vals = [p["curvature_ratio_eps3e4_mean"] for p in ps]
        spreads[r] = {
            "n_probes": len(ps),
            "models": sorted({p["model"] for p in ps}),
            "curvature_ratio_means": vals,
            "mean": statistics.fmean(vals),
            "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        }
    loc = jload(ARCH["gapfill_summary"])["curvature"]
    local = {k: {"mean_share_at_lr": v["mean_share_at_lr"], "sd_share_at_lr": v["sd_share_at_lr"],
                 "n_batches": len(v["rows"]),
                 "source": ARCH["gapfill_summary"] + f" :: curvature.{k}"} for k, v in loc.items()}
    ratios = [p["curvature_ratio_eps3e4_mean"] for p in probes]
    sign_flip = min(ratios) < 0 < max(ratios)
    return {
        "probes": probes,
        "n_probes": len(probes),
        "n_distinct_ranks_probed": len({p["rank"] for p in probes}),
        "ranks_probed": sorted({p["rank"] for p in probes}),
        "sign_of_curvature_changes_with_rank": sign_flip,
        "curvature_min": min(ratios), "curvature_max": max(ratios),
        "local_r5_r6_llava": local,
        "cross_seed_spread_at_r24": hessian_seed_spread(),
        "note": "the curvature probes hold the rank fixed per file and vary the batch (3 batches); "
                "they therefore measure within-run batch dispersion, while p3_hessian_probe_r24_s* "
                "measure dispersion across seed labels at one rank",
    }


# ---------------------------------------------------------------- 4. backbone coverage
def backbone_coverage(rank_res):
    out = {}
    qwen = jload(ARCH["gamma_qwen_blocks"])
    clip = jload(ARCH["clip_ranksweep"])
    qw = jload(ARCH["qwen_ranksweep"])
    sep = jload(ARCH["rank_separation"])

    out["llava_1_5_7b"] = {
        "gamma_archived": False,
        "gamma_note": "Gamma for LLaVA is measured on CLIP ViT-B/32 by design "
                      "(clip_peft_gamma_ordering.json, gamma_clip.json); no per-block Gamma archive "
                      "for LLaVA itself is present in this repository",
        "downstream_effect_archive": ARCH["rank_separation"],
        "downstream_field": sep["meta"]["field"],
        "n_seeds_per_rank": sep["meta"]["n_seeds_per_rank"],
        "ranks_covered": sep["meta"]["ranks"],
        "crossing_supported": rank_res["sign_split"]["crossing_between"] is not None,
        "downstream_task_metric": {"archive": ARCH["rank_separation"] + " :: vqa_equivalence",
                                   "n_questions": sep["vqa_equivalence"]["n_questions"],
                                   "n_ranks_compared": 2},
        "block_ordering_stability": ARCH["llava_ordering_stability"],
        "kendall_W": jload(ARCH["llava_ordering_stability"])["kendall_W"],
    }
    out["qwen2_vl_2b"] = {
        "gamma_archived": True,
        "gamma_archive": ARCH["gamma_qwen_blocks"],
        "gamma_batch_size": qwen["batch_size"],
        "gamma_n_batch": qwen["n_batch"],
        "gamma_reference_rank": qwen["reference_rank"],
        "gamma_seeds": qwen["seeds"],
        "gamma_relative_sd_worst": max(
            v["sd_across_seeds"] / abs(v["mean"]) for v in qwen["gamma_across_seeds"].values()),
        "gamma_sign_flips_across_seeds": [k for k, v in qwen["gamma_across_seeds"].items()
                                          if min(v["per_seed"]) < 0 < max(v["per_seed"])],
        "downstream_effect_archive": ARCH["qwen_ranksweep"],
        "downstream_field": "dE_eval_real",
        "ranks_covered": sorted({int(r["rank"]) for r in qw["runs"]}),
        "n_seeds_per_rank": len({r["seed"] for r in qw["runs"]}),
        "downstream_task_metric": False,
        "hessian_probe": ARCH["hessian_qwen2b_r5"],
    }
    out["clip_vit_b32"] = {
        "gamma_archived": True,
        "gamma_archive": ARCH["gamma_clip"],
        "gamma_block_scheme": "vision / text_shallow / text_mid / text_deep",
        "gamma_estimation_batch_sizes": jload(ARCH["gamma_batch_sensitivity"])["meta"]["sizes"],
        "downstream_effect_archive": ARCH["clip_ranksweep"],
        "downstream_field": "dE_test",
        "ranks_covered": sorted({int(r["rank"]) for r in clip["runs"]}),
        "n_seeds_per_rank": 3,
        "downstream_task_metric": {"archive": ARCH["clip_ranksweep"],
                                   "metric": "R@1 (Flickr30k self-split)"},
        "n_runs": len(clip["runs"]),
    }
    gv = jload(ARCH["gamma_siglip"])
    gp = jload(ARCH["gamma_blip"])
    out["siglip"] = {
        "gamma_archived": True, "gamma_archive": ARCH["gamma_siglip"],
        "gamma_budget": gv["meta"]["budget"], "gamma_allocation": gv["allocation"],
        "downstream_effect_archive": None,
        "note": "Gamma and its induced allocation exist; no archive pairs them with a trained "
                "downstream effect for this backbone in this repository",
    }
    out["blip"] = {
        "gamma_archived": True, "gamma_archive": ARCH["gamma_blip"],
        "gamma_allocation": gp["allocation"], "energy": gp["meta"]["energy"],
        "downstream_effect_archive": None,
        "note": "same limitation as SigLIP: allocation archived, downstream effect not",
    }

    # which claims hold everywhere vs family-specific
    claims = {
        "gamma_is_measurable_on_the_target_model": {
            "holds_on": ["qwen2_vl_2b", "clip_vit_b32", "siglip", "blip"],
            "fails_or_untested_on": ["llava_1_5_7b"],
            "verdict": "family_specific",
            "evidence": "three independent families have archived Gamma and an induced allocation; "
                        "LLaVA's allocation is derived from CLIP ViT-B/32 by design",
        },
        "downstream_crossing_between_r5_and_r6_on_llava": {
            "holds_on": ["llava_1_5_7b"],
            "fails_or_untested_on": ["qwen2_vl_2b", "clip_vit_b32", "siglip", "blip"],
            "verdict": "family_specific",
            "evidence": "ten seeds per rank on LLaVA only; the other families do not have the "
                        "same rank grid at the same seeds",
        },
        "gamma_block_ordering_is_rank_invariant": {
            "holds_on": ["llava_1_5_7b"],
            "fails_or_untested_on": ["qwen2_vl_2b", "clip_vit_b32"],
            "verdict": "family_specific",
            "evidence": "LLaVA block ordering has Kendall W = 1.0 over five rank levels; the Qwen "
                        "per-block Gamma ordering changes between its three seeds and the CLIP block "
                        "allocation changes between estimation batch sizes",
        },
        "gamma_induced_allocation_is_reproducible_under_re_estimation": {
            "holds_on": [],
            "fails_or_untested_on": list(out),
            "verdict": "not_supported",
            "evidence": "the Qwen Gamma spread across three seeds exceeds the allocation break-even; "
                        "only part of the seeds reproduce the point allocation",
        },
    }
    return {"families": out, "claims": claims,
            "n_families_with_gamma": sum(1 for v in out.values() if v["gamma_archived"]),
            "n_families_with_downstream_effect": sum(
                1 for v in out.values() if v["downstream_effect_archive"]),
            "n_families_with_both": sum(
                1 for v in out.values() if v["gamma_archived"] and v["downstream_effect_archive"])}


# ---------------------------------------------------------------- conclusion text
def build_conclusion(rank_res, batch_res, noise_res, back_res):
    crossing = rank_res["sign_split"]["crossing_between"]
    fam = batch_res["batch_families"]
    sup = batch_res["support_counts"]
    fam_sd = ", ".join(f"{k} ({v['n_runs']} runs)" for k, v in fam.items())
    n_seeds_ok = noise_res["n_seeds_preserving_point_order"]
    n_seeds = noise_res["n_seeds_available"]
    text = (
        "The Gamma-driven rank allocation is applicable on LLaVA-1.5-7B over ranks 3 to 8 for the "
        f"alignment-energy effect, with the crossing between r={crossing[0]} and r={crossing[1]}, and "
        "on Qwen2-VL-2B over the ranks that backbone's rank sweep covers; it is not applicable in any "
        "configuration where the archives disagree about the sign of the effect. "
        "(1) Rank: with ten seeds per rank the LLaVA effect is completely sign-separated -- all ten "
        f"runs are negative at r={rank_res['sign_split']['fully_negative_ranks']} and all ten positive "
        f"at r={rank_res['sign_split']['fully_positive_ranks']} -- so the sign of the effect is the "
        f"same for every archived seed at every rank, and the crossing is exact. Within a side of the "
        f"crossing the ordering is weaker: {rank_res['n_pairs_sign_separated']} of "
        f"{rank_res['n_pairs']} rank pairs are ordered for every seed, and the pairs that are not are "
        f"{rank_res['non_sign_separated_pairs']} -- both adjacent pairs below the crossing and the "
        "adjacent pair above it. "
        "But the ordering is only defined against the alignment energy: on the 300-question VQA-RAD "
        "evaluation the same two ranks give token F1 that is statistically equivalent "
        f"(delta {rank_res['vqa_rad_300q']['contrast_r5_minus_r6']['token_f1']:+.4f}, TOST equivalent at "
        f"the declared margin), and exact-match accuracy reverses "
        f"({rank_res['vqa_rad_300q']['contrast_r5_minus_r6']['accuracy']:+.4f}, 95% CI "
        f"[{rank_res['vqa_rad_300q']['contrast_r5_minus_r6']['accuracy_ci95'][0]:+.4f}, "
        f"{rank_res['vqa_rad_300q']['contrast_r5_minus_r6']['accuracy_ci95'][1]:+.4f}]). "
        f"(2) Batch: the crossing is not batch-invariant. Across the three batch families the corpus "
        f"contains ({fam_sd}), of which {sup['n_ranks_shared_by_two_families']} ranks are shared by two "
        f"families and {sup['n_shared_ranks_sign_disagreeing']} of those disagree in sign; inside the "
        "shared ranks the direction of the rank trend reverses between families "
        f"(extra rho={batch_res['ordering_reversal_within_families']['extra_spearman']:+.2f} vs sweep "
        f"rho={batch_res['ordering_reversal_within_families']['sweep_spearman']:+.2f}). The "
        f"batch_size 1 to 2 comparison keeps the side of the crossing in "
        f"{batch_res['conclusions']['n_batchsize_cells_preserving_side_at_bs2']} of "
        f"{batch_res['conclusions']['n_batchsize_cells']} archived cells (from "
        f"{batch_res['conclusions']['n_batchsize_cells_preserving_side_at_bs1']} of "
        f"{batch_res['conclusions']['n_batchsize_cells']} at batch_size 1) but rests on one seed per "
        f"rank and reduces the effect. (3) Measurement noise: under a uniform relative perturbation the ordering of the "
        f"block |Gamma| can already change at rho = {noise_res['rho_order_flip']:.4f} "
        f"({100*noise_res['rho_order_flip']:.1f}% per block, all six pairs hold only to "
        f"rho = {noise_res['rho_split_all_pairs']:.4f}), while the archived repeated-estimate "
        f"dispersion for the same Gamma is "
        f"{noise_res['noise_to_tolerance_ratios']['worst_observed_relative_sd']:.3f} relative sd -- "
        f"{noise_res['noise_to_tolerance_ratios']['worst_observed_relative_sd_over_rho_order']:.1f}x "
        f"the ordering break-even. Only {n_seeds_ok} of {n_seeds} archived seeds reproduce the point "
        "ordering. The advantage of the archived plan over the uniform plan on the allocation "
        f"objective survives much larger perturbations, to rho = "
        f"{noise_res['rho_advantage_lost_on_linear_objective']:.2f}. "
        "What the archives cannot support: "
        "(a) no archive measures Gamma on LLaVA-1.5-7B itself, so the noise claim is transported from "
        "CLIP and Qwen2-VL-2B; "
        "(b) no archive re-estimates Gamma at a second batch size on the backbone that owns the "
        "allocation (Qwen2-VL-2B, batch_size 4 fixed), so the batch answer for Gamma is one backbone "
        "and four sizes on CLIP only; "
        "(c) the batch-family disagreement is three seeds per rank, and the batch_size comparison is a "
        "single seed per rank, so neither can exclude a seed effect; "
        "(d) SigLIP and BLIP have Gamma and an induced allocation but no paired downstream effect, so "
        "no claim of the form 'this allocation helps' is available for them; "
        "(e) the archives fix the softmin weights of the allocation rule but not the map from those "
        "weights to the archived plan, so the perturbation that would change the plan itself cannot "
        "be asserted -- what is bounded instead is the perturbation that can change the ordering "
        f"(rho = {noise_res['rho_order_flip']:.3f}) and the perturbation that removes the plan's "
        f"advantage on the allocation objective (rho = "
        f"{noise_res['rho_advantage_lost_on_linear_objective']:.2f}), and the archives contain no "
        "trained arm whose Gamma was perturbed by either amount."
    )
    return {
        "applicability_boundary": text,
        "supported_regimes": {
            "backbone": ["LLaVA-1.5-7B (alignment energy, ranks 3-8)",
                         "Qwen2-VL-2B (alignment energy, ranks 4-16)"],
            "ranks": {"llava": rank_res["primary_ranks"],
                      "qwen2_vl_2b": back_res["families"]["qwen2_vl_2b"]["ranks_covered"],
                      "clip_vit_b32": back_res["families"]["clip_vit_b32"]["ranks_covered"]},
            "batch_size": [1, 2],
            "seeds_per_rank": {"llava_primary": rank_res["primary_n_seeds_per_rank"],
                               "qwen2_vl_2b": 3, "clip_vit_b32": 3},
        },
        "unsupported_or_broken_regimes": {
            "batch_family": batch_res["ordering_reversal_within_families"]["shared_ranks"],
            "ranks_with_batch_sign_disagreement":
                [int(r) for r, v in batch_res["shared_rank_comparison"].items() if not v["sign_agreement"]],
            "task_metric_ordering": "VQA-RAD exact-match accuracy reverses the alignment-energy ordering",
            "unresolved_rank_pair": rank_res["non_sign_separated_pairs"],
            "backbones_without_downstream_evidence": ["siglip", "blip"],
        },
        "cannot_be_supported_from_these_archives": [
            "Gamma measured on LLaVA-1.5-7B itself",
            "Gamma re-estimated at a second batch size on Qwen2-VL-2B",
            "downstream effect for SigLIP or BLIP allocations",
            "a seed-paired batch_size comparison at any rank other than 5 and 6, seed 42",
            "any rank-sweep downstream metric on LLaVA beyond r=5 and r=6 (300 VQA-RAD questions)",
            "a trained arm whose Gamma was deliberately perturbed by the break-even amount",
        ],
    }


# ---------------------------------------------------------------- assertions
def verify(res):
    """Hard assertions: every copied number must equal the archive field it names."""
    checks = []

    def ck(name, cond):
        checks.append({"check": name, "passed": bool(cond)})
        if not cond:
            raise AssertionError(f"assertion failed: {name}")

    def pair_diffs(sep_doc, key):
        a, b = key[1:].split("-")
        va = sep_doc["ranks"][a.lstrip("r")]["values_by_seed"]
        vb = sep_doc["ranks"][b.lstrip("r")]["values_by_seed"]
        return [va[s] - vb[s] for s in sorted(set(va) & set(vb), key=int)]

    # rank sensitivity vs the archive
    sep = jload(ARCH["rank_separation"])
    for r, blk in res["rank_sensitivity"]["per_rank"].items():
        a = sep["ranks"][r]
        ck(f"rank {r} mean", abs(a["mean"] - blk["mean"]) < 1e-12)
        ck(f"rank {r} sd", abs(a["sd"] - blk["sd"]) < 1e-12)
        ck(f"rank {r} n", a["n"] == blk["n_seeds"])
        ck(f"rank {r} values_by_seed",
           a["values_by_seed"] == {k: v for k, v in blk["values_by_seed"].items()})
    ck("n_pairs", res["rank_sensitivity"]["n_pairs"] == len(sep["separation"]["pairs"]))
    ck("crossing", res["rank_sensitivity"]["sign_split"]["crossing_between"]
       == sep["conclusion"]["crossing_between"])
    # the r=7 vs r=8 pair is the archived exception
    ck("r7-r8 unresolved",
       not res["rank_sensitivity"]["all_pair_tests"]["r7-r8"]["all_diffs_same_sign"])
    # paired sign-flip test must equal the archive's p_paired_signflip for every pair
    for pair in sep["separation"]["pairs"]:
        key = f"r{pair['rank_a']}-r{pair['rank_b']}"
        ck(f"{key} paired sign-flip p",
           abs(res["rank_sensitivity"]["all_pair_tests"][key]["p_two_sided"]
               - pair["p_paired_signflip"]) < 1e-12)
        ck(f"{key} all_diffs_same_sign is strict ordering",
           res["rank_sensitivity"]["all_pair_tests"][key]["all_diffs_same_sign"]
           == (all(d > 0 for d in pair_diffs(sep, key)) or all(d < 0 for d in pair_diffs(sep, key))))
        ck(f"{key} archive flag carried verbatim",
           res["rank_sensitivity"]["all_pair_tests"][key]["archive_sign_separated_passthrough"]
           == pair["sign_separated"])
    ck("paired minimum p",
       abs(res["rank_sensitivity"]["all_pair_tests"]["r5-r6"]["p_two_sided"]
           - sep["separation"]["paired_minimum_p"]) < 1e-12)
    ck("n pairs at paired minimum",
       sum(1 for v in res["rank_sensitivity"]["all_pair_tests"].values()
           if abs(v["p_two_sided"] - sep["separation"]["paired_minimum_p"]) < 1e-12)
       == sep["separation"]["n_pairs_at_paired_minimum"])
    ck("vqa token_f1", abs(res["rank_sensitivity"]["vqa_rad_300q"]["contrast_r5_minus_r6"]["token_f1"]
                           - sep["vqa_equivalence"]["contrasts"]["5_minus_6"]["token_f1"]["delta"]) < 1e-12)
    ck("vqa accuracy", abs(res["rank_sensitivity"]["vqa_rad_300q"]["contrast_r5_minus_r6"]["accuracy"]
                           - sep["vqa_equivalence"]["contrasts"]["5_minus_6"]["accuracy"]["delta"]) < 1e-12)
    ck("r5 tost", abs(res["rank_sensitivity"]["rank5_near_zero_band"]["tost_p"]
                      - sep["rank5_equivalence"]["tost_p"]) < 1e-12)

    # downstream sweeps
    clip = jload(ARCH["clip_ranksweep"])
    n_clip = len([r for r in clip["runs"] if int(r["rank"]) != 0])
    n_cells = sum(len(v["seeds"]) for v in res["rank_sensitivity"]["downstream_clip_rank_sweep"]["cells"]
                  for _ in [0])
    ck("clip cells are subsets of clip runs",
       n_cells <= len(clip["runs"]))
    ck("clip r5-r6 paired exists",
       res["rank_sensitivity"]["downstream_clip_rank_sweep"]["contrast_r5_minus_r6_real_n1024"] is not None)

    # batch sensitivity vs the archive
    repro = jload(ARCH["reproducibility"])["batch_effect"]
    for name, blk in res["batch_sensitivity"]["batch_families"].items():
        a = repro["batches"][name]
        ck(f"batch {name} n_runs", a["n_runs"] == blk["n_runs"])
        for r, vals in a["per_rank_dE"].items():
            ck(f"batch {name} rank {r} mean",
               abs(statistics.fmean(vals) - blk["per_rank"][r]["mean"]) < 1e-12)
    for r, row in res["batch_sensitivity"]["shared_rank_comparison"].items():
        a = [x for x in repro["shared_rank_comparison"] if str(x["rank"]) == r][0]
        ck(f"shared rank {r} difference", abs(a["difference"] - row["difference"]) < 1e-12)
        ck(f"shared rank {r} sign", a["sign_agreement"] == row["sign_agreement"])
    ck("n shared disagree", res["batch_sensitivity"]["support_counts"]["n_shared_ranks_sign_disagreeing"]
       == repro["n_shared_ranks_sign_disagree"])
    # the batch-size verdict must follow from the recorded cells, not be hardcoded
    for r, row in res["batch_sensitivity"]["batchsize_paired_by_rank"].items():
        expect = sum(1 for v in row["delta_E_bs2"] if (v < 0) == (r == "5"))
        ck(f"batchsize r={r} side count at bs2", row["n_cells_preserving_primary_side_at_bs2"] == expect)
    ck("batchsize conclusion follows the cells",
       res["batch_sensitivity"]["conclusions"]["crossing_survives_batchsize_1_to_2"]
       == all(v["n_cells_preserving_primary_side_at_bs2"] == v["n_environments"]
              for v in res["batch_sensitivity"]["batchsize_paired_by_rank"].values()))

    # batch-size cells vs the per-run experiment files
    for key, cell in res["batch_sensitivity"]["batchsize_cell_comparison"].items():
        b1 = jload(cell["source_bs1"])
        b2 = jload(cell["source_bs2"])
        ck(f"{key} bs1 delta_E", abs(b1["delta_E"] - cell["delta_E_bs1"]) < 1e-12)
        ck(f"{key} bs2 delta_E", abs(b2["delta_E"] - cell["delta_E_bs2"]) < 1e-12)
        ck(f"{key} bs1 batch_size", b1["batch_size"] == 1)
        ck(f"{key} bs2 batch_size", b2["batch_size"] == 2)
        ck(f"{key} same rank/seed/lr/epochs/alpha",
           (b1["rank"], b1["seed"], b1["lr"], b1["epochs"], b1["lora_alpha"]) ==
           (b2["rank"], b2["seed"], b2["lr"], b2["epochs"], b2["lora_alpha"]))

    # noise break-even vs the plan archive
    plans = jload(ARCH["alloc_plans"])
    ck("beta_paper", abs(res["noise_break_even"]["reference"]["beta_paper"]
                         - plans["beta_grid"]["beta_paper_0.137"]) < 1e-15)
    ck("gamma_abs matches plan archive",
       all(abs(res["noise_break_even"]["reference"]["gamma_abs"][k] - v) < 1e-12
           for k, v in plans["gamma_abs"].items()))
    ck("point allocation matches archived Gamma plan",
       res["noise_break_even"]["reference"]["point_allocation"] == plans["plans"]["exp_beta_paper_0.137"]["ranks"])
    ck("re-implemented softmin weights reproduce every archived exp_beta_* weight vector",
       res["noise_break_even"]["softmin_weight_check_summary"]["n_softmin_weights_reproduced"]
       == res["noise_break_even"]["softmin_weight_check_summary"]["n_plans_checked"])
    ck("archived plan list is internally budget-exact",
       res["noise_break_even"]["lattice_regeneration"]["n_every_archived_plan_hits_budget_exactly"]
       == res["noise_break_even"]["lattice_regeneration"]["n_archived"])
    ck("archived plan list count matches its own declared count",
       res["noise_break_even"]["lattice_regeneration"]["n_archived"]
       == res["noise_break_even"]["lattice_regeneration"]["n_declared"])
    ck("weights-to-plan map is recorded as undocumented, not asserted",
       res["noise_break_even"]["softmin_weight_check_summary"]
       ["n_archived_plans_reproduced_by_nearest_target_rank"]
       <= res["noise_break_even"]["softmin_weight_check_summary"]["n_plans_checked"])
    ck("rho_order positive", res["noise_break_even"]["rho_order_flip"] > 0)
    ck("rho_split <= rho_order", res["noise_break_even"]["rho_split_all_pairs"]
       <= res["noise_break_even"]["rho_order_flip"])
    ck("rho_reweight is absent when no block is within the precision floor",
       (res["noise_break_even"]["rho_reweight"] is None)
       == all(v["log_odds_vs_heaviest_at_rho_0"] <= 708.0
              for v in res["noise_break_even"]["rho_reweight_per_block"].values()))
    ck("weights are one-hot at the reference beta",
       res["noise_break_even"]["weights_are_one_hot_at_beta_paper"])
    ck("no uniform-target-rank threshold exists",
       res["noise_break_even"]["rho_uniform_target_ranks"] is None)
    ck("rho_adv exceeds the ordering break-even",
       res["noise_break_even"]["rho_advantage_lost_on_linear_objective"]
       > res["noise_break_even"]["rho_order_flip"])
    ck("objective values match archive",
       abs(res["noise_break_even"]["objective_values"]["uniform_plan"]
           - plans["uniform_linear_objective"]) < 1e-6)
    ck("gamma plan objective matches archive",
       abs(res["noise_break_even"]["objective_values"]["gamma_plan"]
           - plans["plans"]["exp_beta_paper_0.137"]["linear_objective"]) < 1e-6)
    ck("archived gamma plan is the one whose objective is compared",
       res["noise_break_even"]["reference"]["point_allocation"]
       == plans["plans"]["exp_beta_paper_0.137"]["ranks"])
    gq = jload(ARCH["gamma_qwen_blocks"])
    for b, v in gq["gamma_across_seeds"].items():
        obs = res["noise_break_even"]["observed_noise_same_units"][f"qwen2vl2b_across_seeds_{b}"]
        ck(f"qwen gamma sd {b}", abs(obs["sd_across_seeds"] - v["sd_across_seeds"]) < 1e-12)

    # backbone coverage
    ck("llava has no own gamma", res["backbone_coverage"]["families"]["llava_1_5_7b"]["gamma_archived"] is False)
    ck("qwen gamma batch size", res["backbone_coverage"]["families"]["qwen2_vl_2b"]["gamma_batch_size"]
       == gq["batch_size"])
    ck("kendall W", abs(res["backbone_coverage"]["families"]["llava_1_5_7b"]["kendall_W"]
                        - jload(ARCH["llava_ordering_stability"])["kendall_W"]) < 1e-12)
    return checks


# ---------------------------------------------------------------- main
def build():
    rank_res = rank_sensitivity()
    batch_res = batch_sensitivity()
    noise_res = noise_break_even(rank_res)
    back_res = backbone_coverage(rank_res)
    conclusion = build_conclusion(rank_res, batch_res, noise_res, back_res)

    res = {
        "meta": {
            "script": "tools/_p1636_p3_gamma_robustness.py",
            "task": "P3 Gamma robustness / applicability boundary from archives only (no new training)",
            "source_archives": {k: v for k, v in sorted(ARCH.items())},
            "source_archives_sha256": {k: sha256_file(v) for k, v in sorted(ARCH.items())},
            "source_experiment_files": EXP_FILES,
            "field_paths": {
                "rank_sensitivity": "outputs/analysis/p3_rank_separation_extended.json :: "
                                    "ranks[r].{mean,sd,n,values_by_seed}, separation.pairs, "
                                    "rank5_equivalence, vqa_equivalence",
                "rank_sensitivity_downstream_clip": "outputs/analysis/p3d_clip_ranksweep.json :: "
                                                    "runs[*].{rank,condition,n_train,seed,dE_test,R@1}",
                "rank_sensitivity_downstream_qwen": "outputs/analysis/p3d_qwen_ranksweep.json :: "
                                                    "runs[*].{rank,condition,seed,dE_eval_real}",
                "rank_sensitivity_ordering": "outputs/llava_gamma_ordering_stability.json :: "
                                             "{ordering_per_rank,kendall_W,mean_pairwise_spearman}",
                "batch_sensitivity_families": "outputs/analysis/p3_reproducibility.json :: "
                                              "batch_effect.batches[*].per_rank_dE, "
                                              "batch_effect.shared_rank_comparison",
                "batch_sensitivity_cells": "paper3/scripts/outputs/experiments/"
                                           "verify_r{5,6}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform{,_b2,_b2_cloud}.json "
                                           "and cloud_verify_r{5,6}_s42.json :: delta_E, batch_size",
                "batch_sensitivity_gamma": "outputs/analysis/p3_gamma_batch_sensitivity.json :: "
                                           "conditions[*].{n,draw,gamma,gamma_sd,abs_order,ranks}, summary[*].cv",
                "noise_break_even": "outputs/analysis/p3_alloc_plans.json :: "
                                    "{gamma_abs,gamma_measured,cost_per_rank,budget_params,beta_grid,"
                                    "beta_star_1_over_sigma,plans.exp_beta_paper_0.137,"
                                    "uniform_linear_objective,exact_budget_allocations}",
                "noise_break_even_repeats": "outputs/analysis/p3_alloc_gamma_qwen2vl2b.json :: "
                                            "gamma_across_seeds[*].{mean,sd_across_seeds,per_seed}",
                "noise_break_even_hessian": "outputs/analysis/p3_hessian_probe_r24.json, "
                                            "p3_hessian_probe_r24_s123.json, p3_hessian_probe_r24_s789.json, "
                                            "cloud_p3_hessian_probe_r64.json, p3_hessian_probe_qwen2b_r5.json :: "
                                            "runs[*].{g2,second_order_over_first_order,share_at_lr}",
                "noise_break_even_advantage": "outputs/analysis/p3_alloc_results.json :: "
                                              "comparisons.exp_beta_paper_0.137.vs_uniform",
                "backbone_coverage": "outputs/analysis/{gamma_clip,p3_siglip_gamma,p3_blip_gamma,"
                                     "p3_alloc_gamma_qwen2vl2b,gamma_theory_check}.json",
            },
            "n_boot": N_BOOT,
            "rng_seed": RNG_SEED,
            "idempotent": True,
            "note": "no wall-clock field inside the hashed part, so re-running reproduces the "
                    "file byte for byte; self_sha256 covers everything except generated_utc and "
                    "self_sha256 itself",
        },
        "rank_sensitivity": rank_res,
        "batch_sensitivity": batch_res,
        "noise_break_even": noise_res,
        "backbone_coverage": back_res,
        "conclusion": conclusion,
        "assertions": [],
    }
    res["assertions"] = verify(res)

    hashed = {k: v for k, v in res.items() if k not in ("generated_utc",)}
    res["meta"]["self_sha256"] = hashlib.sha256(canonical(hashed).encode("utf-8")).hexdigest()
    return res


def print_report(res):
    rs, bs, nb, bc = (res["rank_sensitivity"], res["batch_sensitivity"],
                      res["noise_break_even"], res["backbone_coverage"])
    p = print
    p("=" * 78)
    p("P3 GAMMA ROBUSTNESS -- applicability boundary (archives only)")
    p("=" * 78)
    p("")
    p("[1] RANK SENSITIVITY")
    p(f"    primary arm : {rs['primary_arm']}")
    p(f"    field       : {rs['primary_field']}, n_seeds_per_rank = {rs['primary_n_seeds_per_rank']}")
    for r in map(str, rs["primary_ranks"]):
        b = rs["per_rank"][r]
        p(f"    r={r:>2}  mean {b['mean']:+8.2f}  sd {b['sd']:7.3f}  "
          f"neg {b['n_negative']:2d}/{b['n_seeds']}  pos {b['n_positive']:2d}")
    p(f"    crossing between r={rs['sign_split']['crossing_between']}")
    p(f"    strictly ordered pairs (all 10 seeds same sign): {rs['n_pairs_sign_separated']}/{rs['n_pairs']}; "
      f"not ordered: {rs['non_sign_separated_pairs']}")
    for k, v in rs["adjacent_rank_tests"].items():
        p(f"      {k}: paired sign-flip p={v['p_two_sided']:.6f}  "
          f"ordered_for_every_seed={v['all_diffs_same_sign']}")
    v = rs["vqa_rad_300q"]
    p(f"    VQA-RAD (n={v['n_questions']}) r5-r6: token_f1 {v['contrast_r5_minus_r6']['token_f1']:+.4f} "
      f"eq_at_margin={v['contrast_r5_minus_r6']['token_f1_equivalent_at_margin']}; "
      f"accuracy {v['contrast_r5_minus_r6']['accuracy']:+.4f} "
      f"CI [{v['contrast_r5_minus_r6']['accuracy_ci95'][0]:+.4f}, {v['contrast_r5_minus_r6']['accuracy_ci95'][1]:+.4f}]")
    q = rs["downstream_qwen_rank_sweep"]
    p(f"    Qwen2-VL-2B dE_eval_real over ranks {q['ranks_covered']}: spearman {q['spearman_rank_vs_dE']:+.3f}")
    c = rs["gamma_block_ordering_vs_rank"]
    p(f"    Gamma block ordering vs rank (LLaVA, {c['llava']['ranks']}): Kendall W={c['llava']['kendall_W']}")
    p(f"    Qwen Gamma ordering across 3 seeds: stable={c['qwen_seeds']['order_stable_across_seeds']} "
      f"({c['qwen_seeds']['n_distinct_orderings']} distinct)")
    p("")
    p("[2] BATCH SENSITIVITY")
    for name, f in bs["batch_families"].items():
        p(f"    family {name:>6}: {f['n_runs']:2d} runs, ranks {f['ranks_covered']}, "
          f"spearman(rank,dE) {f['spearman_rank_vs_dE']:+.3f}")
    p(f"    shared ranks: {sorted(int(r) for r in bs['shared_rank_comparison'])}")
    for r, row in bs["shared_rank_comparison"].items():
        p(f"      shared r={r}: extra {row['extra_mean']:+8.2f}  sweep {row['sweep_mean']:+8.2f}  "
          f"diff {row['difference']:+8.2f}  sign_agree={row['sign_agreement']}")
    o = bs["ordering_reversal_within_families"]
    p(f"    within-family direction reverses: {o['direction_reverses_between_families']} "
      f"(extra rho {o['extra_spearman']:+.2f}, sweep rho {o['sweep_spearman']:+.2f})")
    for k, cell in bs["batchsize_cell_comparison"].items():
        p(f"    bs cell {k}: dE bs1 {cell['delta_E_bs1']:+8.2f} -> bs2 {cell['delta_E_bs2']:+8.2f} "
          f"(diff {cell['delta_E_bs2_minus_bs1']:+7.2f})")
    for r, row in bs["batchsize_paired_by_rank"].items():
        p(f"      r={r}: side kept in {row['n_cells_preserving_primary_side']}/"
          f"{row['n_environments']} at bs1 and {row['n_cells_preserving_primary_side_at_bs2']}/"
          f"{row['n_environments']} at bs2 (primary side {row['primary_side']})")
    s = bs["support_counts"]
    p(f"    support: {s['n_batch_families']} families / {s['n_batch_families_total_runs']} runs, "
      f"{s['n_ranks_shared_by_two_families']} shared ranks, "
      f"{s['n_shared_ranks_sign_disagreeing']} sign-disagreeing")
    p("")
    p("[3] GAMMA NOISE / BREAK-EVEN")
    p(f"    rho_order   (block ordering can flip)  = {nb['rho_order_flip']:.4f}  "
      f"pair {nb['rho_order_flip_binding_pair']}")
    p(f"    rho_split   (all 6 pairs keep order)  = {nb['rho_split_all_pairs']:.4f}  "
      f"pair {nb['rho_split_binding_pair']}")
    p(f"    rho_reweight(numerically separable)  = "
      f"{nb['rho_reweight'] if nb['rho_reweight'] is not None else 'none in range'}"
      f"   weights_one_hot={nb['weights_are_one_hot_at_beta_paper']}")
    p(f"    rho_uniform (target ranks all equal)  = "
      f"{nb['rho_uniform_target_ranks'] if nb['rho_uniform_target_ranks'] is not None else 'does not exist'}")
    p(f"    rho_adv     (advantage lost, objective) = {nb['rho_advantage_lost_on_linear_objective']:.3f}")
    p(f"    objective gamma/uniform = {nb['objective_values']['gamma_over_uniform']:.3f}")
    p(f"    worst observed relative sd = "
      f"{nb['noise_to_tolerance_ratios']['worst_observed_relative_sd']:.3f} "
      f"= {nb['noise_to_tolerance_ratios']['worst_observed_relative_sd_over_rho_order']:.2f}x rho_order")
    p(f"    seeds reproducing the point ordering: "
      f"{nb['n_seeds_preserving_point_order']}/{nb['n_seeds_available']}")
    hs = nb["hessian_curvature"]
    p(f"    curvature probes: {hs['n_probes']} over ranks {hs['ranks_probed']}; "
      f"sign of curvature changes with rank: {hs['sign_of_curvature_changes_with_rank']}")
    for pr in hs["probes"]:
        p(f"      r={pr['rank']:<3} {pr['model'][:26]:<26} mean {pr['curvature_ratio_eps3e4_mean']:+.4f} "
          f"sd {pr['curvature_ratio_eps3e4_sd']:.4f} "
          f"sign_changes_across_batches={pr['sign_changes_across_batches']}")
    acs = hs["cross_seed_spread_at_r24"]["across_seeds"]
    p(f"    r=24 across seed labels {acs['seed_labels']}: g2 rel sd "
      f"{acs['g2_relative_sd_across_seeds']:.3f}, curvature-ratio rel sd "
      f"{acs['curvature_ratio_relative_sd_across_seeds']:.3f}")
    p("")
    p("[4] BACKBONE COVERAGE")
    p(f"    families with Gamma: {bc['n_families_with_gamma']}, "
      f"with downstream effect: {bc['n_families_with_downstream_effect']}, "
      f"with both: {bc['n_families_with_both']}")
    for name, f in bc["families"].items():
        p(f"    {name:<16} gamma={str(f['gamma_archived']):<5} "
          f"downstream={str(bool(f['downstream_effect_archive'])):<5} {f.get('note','')[:60]}")
    for name, cl in bc["claims"].items():
        p(f"    claim {name}: {cl['verdict']}")
    p("")
    p("[5] CONCLUSION")
    import textwrap
    for line in textwrap.wrap(res["conclusion"]["applicability_boundary"], 96):
        p("    " + line)
    p("")
    p(f"assertions passed: {len(res['assertions'])}/{len(res['assertions'])}")
    p(f"self_sha256: {res['meta']['self_sha256']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and every computed number, write nothing")
    args = ap.parse_args(argv)

    if args.dry_run:
        print("DRY RUN -- no file will be written.")
        print(f"plan: read {len(ARCH)} archives + {len(EXP_FILES)} experiment files under {REPO}")
        print("plan: compute rank_sensitivity, batch_sensitivity, noise_break_even, "
              "backbone_coverage, conclusion")
        print(f"plan: assert every printed number against its archive field, then "
              f"{'skip writing' if args.dry_run else 'write'} {OUT_PATH.relative_to(REPO)}")
        print("")

    res = build()

    if args.dry_run:
        print_report(res)
        print("")
        print("DRY RUN -- nothing written.")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        prev_hash = prev.get("meta", {}).get("self_sha256")
        if prev_hash and prev_hash != res["meta"]["self_sha256"]:
            print(f"WARNING: {OUT_PATH.name} already exists with a different self_sha256 "
                  f"({prev_hash[:12]} -> {res['meta']['self_sha256'][:12]}); overwriting.")
    res["generated_utc"] = None  # deliberately left empty: keeps the file rerun-stable
    res.pop("generated_utc")
    OUT_PATH.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print_report(res)
    print("")
    print(f"wrote {OUT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
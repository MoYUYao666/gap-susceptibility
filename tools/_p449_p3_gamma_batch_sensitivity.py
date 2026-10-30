#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p449_p3_gamma_batch_sensitivity.py -- P3 review item R3.4.

"how is this expectation estimated in practice, and how sensitive is Gamma_k to
 the choice and size of the reference batch?"

Two independent archived sources are analysed:

 A. paper3/scripts/outputs/experiments/gamma_llava_results.json
    The exact protocol behind the paper's Appendix-D Table (per-block Gamma_k at
    5 ranks, `config.batches = 5`) and behind Figure/Table statements about
    "5-prompt average".  Records only the AGGREGATE per rank, so the batch effect
    is NOT recoverable from it -- reported as a provenance limitation.

 B. outputs/llava_gamma_batches.json   (produced by tools/llava_gamma_batch_ci.py)
    Per-sample per-block <grad E, grad L> over 6 disjoint 16-image batches
    (96 samples total), same LLaVA blocks.  This DOES support a full
    batch-size / batch-choice sensitivity analysis, and is used for it.

    Caveat stated explicitly: (B) uses real marine images + a fixed QA prompt and
    per-parameter (not LoRA) gradients, whereas the paper's Gamma table uses
    blank images and LoRA adapters.  Conclusions are therefore about the
    ESTIMATOR's stability, not a re-measurement of the paper's exact numbers.

Statistics reported: per-block cross-batch mean/sd/95% t-CI/CV, per-sample
standard error, required n for a target CI width, leave-one-batch-out stability,
rank agreement across batches, and the resulting allocation vector under
different reference batches and sizes.

Output: outputs/analysis/p3_gamma_batch_sensitivity.json
"""
import itertools
import json
import math
import os
from collections import Counter, defaultdict

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "analysis")

PAPER_GAMMA = "paper3/scripts/outputs/experiments/gamma_llava_results.json"
BATCHES = "outputs/llava_gamma_batches.json"

BLOCKS = ["vis", "proj", "llm_shallow", "llm_mid", "llm_deep", "llm_other", "lm_head"]
ALLOC_BLOCKS = ["llm_shallow", "llm_mid", "llm_deep"]
LAYERS_PER_BLOCK = {"llm_shallow": 8, "llm_mid": 16, "llm_deep": 8}
BUDGET = 136          # same rank-layer budget the paper uses (C=64)
RNG = np.random.default_rng(20261012)

with open(os.path.join(ROOT, BATCHES), encoding="utf-8") as f:
    D = json.load(f)
with open(os.path.join(ROOT, PAPER_GAMMA), encoding="utf-8") as f:
    PG = json.load(f)

raw = {k: v for k, v in D["raw_per_sample_blocks"].items()}
batch_keys = sorted(raw, key=int)
N_PER_BATCH = D["n_per_batch"]


def block_mean(samples, b):
    return float(np.mean([s.get(b, 0.0) for s in samples]))


# ---- A. what the paper's own Gamma file records (provenance audit)
paper_gamma_audit = {
    "file": PAPER_GAMMA,
    "config_field": PG["config"],
    "fields_recorded_per_rank": sorted(PG["results_by_rank"]["r8"].keys()),
    "has_per_batch_values": any("batch" in k.lower() for k in PG["results_by_rank"]["r8"].keys()),
    "n_prompts_declared": PG["config"]["batches"],
    "conclusion": ("the published Gamma table stores only the mean over the "
                   "%d-prompt reference batch; the individual prompt values are not "
                   "archived, so the reference-batch sensitivity of the paper's own "
                   "Appendix-D numbers cannot be reconstructed from this file"
                   % PG["config"]["batches"]),
}

# ---- B1. cross-batch statistics
per_block = {}
for b in BLOCKS:
    means = np.asarray([block_mean(raw[k], b) for k in batch_keys], dtype=float)
    all_samples = np.asarray([s.get(b, 0.0) for k in batch_keys for s in raw[k]], dtype=float)
    if len(means) > 1 and means.std(ddof=1) > 0:
        ci = stats.t.interval(0.95, len(means) - 1, loc=means.mean(), scale=stats.sem(means))
    else:
        ci = (means.mean(), means.mean())          # zero-variance block (lm_head): CI degenerates
    per_block[b] = {
        "cross_batch_mean": float(means.mean()),
        "cross_batch_sd": float(means.std(ddof=1)) if len(means) > 1 else None,
        "cross_batch_ci95": [float(ci[0]), float(ci[1])],
        "cross_batch_cv_pct": float(100 * means.std(ddof=1) / abs(means.mean()))
        if (len(means) > 1 and means.mean() != 0) else None,
        "per_batch_means": [float(x) for x in means],
        "per_sample_mean": float(all_samples.mean()),
        "per_sample_sd": float(all_samples.std(ddof=1)),
        "per_sample_sem": float(all_samples.std(ddof=1) / math.sqrt(all_samples.size)),
        "n_samples_total": int(all_samples.size),
        "abs_cross_batch_range": float(means.max() - means.min()),
        "abs_ratio_max_over_min": (float(abs(means).max() / abs(means).min())
                                   if abs(means).min() > 0 else None),
    }

# ---- B2. batch-SIZE sensitivity: subsample m batches x k samples, many draws
def alloc_from_mean(blocks_mean):
    vals = np.asarray([abs(blocks_mean[b]) for b in ALLOC_BLOCKS], dtype=float)
    vals_n = np.asarray([abs(blocks_mean[b]) / LAYERS_PER_BLOCK[b] for b in ALLOC_BLOCKS], dtype=float)
    out = {}
    for tag, v in (("raw", vals), ("param_normalized", vals_n)):
        sigma = v.std()
        beta = 1.0 / sigma if sigma > 0 else 0.0
        share = np.exp(-beta * v)
        share = share / share.sum()
        out[tag] = [int(max(1, round(x))) for x in (share * BUDGET)]
    return out


def order_of(blocks_mean, key=abs):
    return tuple(sorted(BLOCKS, key=lambda b: -key(blocks_mean[b])))


size_sens = {}
for n_batches in (1, 2, 3, 6):
    for k in (1, 4, 8, 16):
        if k > N_PER_BATCH:
            continue
        orders = Counter()
        allocs = Counter()
        vis_vals = []
        draws = 2000
        for _ in range(draws):
            pick_b = RNG.choice(batch_keys, size=n_batches, replace=True)
            acc = defaultdict(list)
            for bk in pick_b:
                samples = raw[bk]
                idx = RNG.integers(0, len(samples), size=k)
                for i in idx:
                    for b in BLOCKS:
                        acc[b].append(samples[i].get(b, 0.0))
            bm = {b: float(np.mean(acc[b])) for b in BLOCKS}
            orders[order_of(bm)] += 1
            a = alloc_from_mean(bm)
            allocs[(tuple(a["raw"]), tuple(a["param_normalized"]))] += 1
            vis_vals.append(bm["vis"])
        size_sens["%db_x%ds" % (n_batches, k)] = {
            "n_ref_batches": n_batches, "n_samples_per_batch": k,
            "n_effective_samples": n_batches * k, "n_draws": draws,
            "top_order": list(orders.most_common(1)[0][0]),
            "top_order_freq": orders.most_common(1)[0][1] / draws,
            "n_distinct_orders": len(orders),
            "top_alloc_raw": list(allocs.most_common(1)[0][0][0]),
            "top_alloc_param_norm": list(allocs.most_common(1)[0][0][1]),
            "top_alloc_freq": allocs.most_common(1)[0][1] / draws,
            "vis_mean": float(np.mean(vis_vals)),
            "vis_sd": float(np.std(vis_vals, ddof=1)),
            "vis_ci95": [float(np.percentile(vis_vals, 2.5)), float(np.percentile(vis_vals, 97.5))],
            "vis_cv_pct": float(100 * np.std(vis_vals, ddof=1) / abs(np.mean(vis_vals))),
        }

# ---- B3. leave-one-batch-out
lobo = {}
for hold in batch_keys:
    keep = [k for k in batch_keys if k != hold]
    bm_all = {b: block_mean([s for k in batch_keys for s in raw[k]], b) for b in BLOCKS}
    bm_keep = {b: block_mean([s for k in keep for s in raw[k]], b) for b in BLOCKS}
    lobo["holdout_" + hold] = {
        "order_kept": list(order_of(bm_keep)),
        "order_all": list(order_of(bm_all)),
        "order_identical": order_of(bm_keep) == order_of(bm_all),
        "alloc_all": alloc_from_mean(bm_all),
        "alloc_without_holdout": alloc_from_mean(bm_keep),
        "vis_shift_pct": float(100 * (bm_keep["vis"] - bm_all["vis"]) / abs(bm_all["vis"])),
    }
lobo_summary = {
    "n_holdouts": len(lobo),
    "n_order_identical": sum(1 for v in lobo.values() if v["order_identical"]),
    "max_abs_vis_shift_pct": max(abs(v["vis_shift_pct"]) for v in lobo.values()),
}
all_alloc_raw = [tuple(v["alloc_without_holdout"]["raw"]) for v in lobo.values()]
all_alloc_raw.append(tuple(alloc_from_mean({b: block_mean([s for k in batch_keys for s in raw[k]], b)
                                            for b in BLOCKS})["raw"]))
lobo_summary["alloc_raw_distinct"] = sorted(set(all_alloc_raw))
lobo_summary["alloc_raw_max_spread"] = [
    max(a[i] for a in all_alloc_raw) - min(a[i] for a in all_alloc_raw) for i in range(len(ALLOC_BLOCKS))]

# ---- B4. sample-size needed for a target CI width on the *worst* block
def n_required(sd, target_half_width):
    # half width = t * sd / sqrt(n) ~ 1.96 sd / sqrt(n) for n large
    return int(math.ceil((1.96 * sd / target_half_width) ** 2))


worst = max(per_block, key=lambda b: abs(per_block[b]["cross_batch_sd"] or 0)
            / (abs(per_block[b]["cross_batch_mean"]) or 1))
n_req = {}
for b in BLOCKS:
    m = per_block[b]["cross_batch_mean"]
    s = per_block[b]["cross_batch_sd"]
    if s is None or s == 0:
        n_req[b] = None
        continue
    n_req[b] = {"relative_sd_pct": 100 * s / abs(m) if m else None,
                "n_for_5pct_ci": n_required(s, 0.05 * abs(m)) if m else None,
                "n_for_10pct_ci": n_required(s, 0.10 * abs(m)) if m else None}

# ---- B5. what an uncertainty budget for the PAPER's own 5-prompt table would be.
#     The paper averages over `config.batches = 5` prompts.  The archive keeps only
#     the mean, so no prompt-level spread is recoverable -> we transfer the relative
#     cross-batch dispersion measured in (B) onto the published point estimates.
#     s/sqrt(n) cancels the block's own sd, so the SE is a RATIO-based projection,
#     not a measurement of the paper's batch.
N_PROMPTS_PAPER = PG["config"]["batches"]
paper_gamma_se = {}
for rk, rv in PG["results_by_rank"].items():
    row = {}
    for b, val in rv["per_block"].items():
        pb = per_block.get(b)
        if pb is None or pb["cross_batch_sd"] is None or pb["cross_batch_mean"] == 0:
            row[b] = {"gamma": val, "sd_imposed": None, "se_5_prompt": None,
                      "ci95_5_prompt": None, "ci_excludes_zero": None}
            continue
        rel = pb["cross_batch_sd"] / abs(pb["cross_batch_mean"])
        sd_imposed = rel * abs(val)
        se = sd_imposed / math.sqrt(N_PROMPTS_PAPER)
        row[b] = {
            "gamma": val,
            "rel_sd_transferred_pct": 100 * rel,
            "sd_imposed": sd_imposed,
            "se_5_prompt": se,
            "ci95_5_prompt": [val - 1.96 * se, val + 1.96 * se],
            "ci_excludes_zero": bool((val - 1.96 * se) * (val + 1.96 * se) > 0),
        }
    paper_gamma_se[rk] = row
paper_gamma_uncertainty = {
    "method": ("relative cross-batch dispersion from source (B) transferred onto the "
               "published point estimates from source (A), divided by sqrt(5 prompts)"),
    "why_not_a_measurement": ("the paper's Gamma file stores only the 5-prompt mean, so "
                              "the prompt-level spread does not exist in the archive; "
                              "this projection says how large the error bar COULD be "
                              "if the block dispersions are comparable"),
    "n_prompts": N_PROMPTS_PAPER,
    "per_rank": paper_gamma_se,
}
paper_gamma_uncertainty["sign_risks"] = [
    {"rank": rk, "block": b, "gamma": v["gamma"],
     "ci95": v["ci95_5_prompt"], "ci_excludes_zero": v["ci_excludes_zero"]}
    for rk, row in paper_gamma_se.items() for b, v in row.items()
    if v["ci95_5_prompt"] is not None and not v["ci_excludes_zero"]
]

out = {
    "meta": {
        "script": "tools/_p449_p3_gamma_batch_sensitivity.py",
        "task": "task-11 (P3 R3.4)",
        "sources": {
            "paper_gamma_table": PAPER_GAMMA,
            "cross_batch_gamma": BATCHES,
        },
        "cross_batch_protocol": D["protocol"],
        "cross_batch_caveat": ("real marine images + fixed QA prompt + per-parameter "
                               "gradients; the paper's own Gamma table uses blank images "
                               "+ LoRA adapters, so these are ESTIMATOR-stability "
                               "results, not a re-measurement of the published values"),
        "rng_seed": 20261012,
        "alloc_blocks": ALLOC_BLOCKS,
        "budget_rank_layers": BUDGET,
    },
    "paper_gamma_table_provenance": paper_gamma_audit,
    "paper_gamma_table_uncertainty_projection": paper_gamma_uncertainty,
    "cross_batch_statistics": per_block,
    "batch_size_and_choice_sensitivity": size_sens,
    "leave_one_batch_out": {"detail": lobo, "summary": lobo_summary},
    "samples_needed_for_ci": n_req,
    "most_unstable_block": worst,
}
dst = os.path.join(OUTDIR, "p3_gamma_batch_sensitivity.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("=" * 78)
print("A. PAPER'S OWN GAMMA TABLE -- what is archived")
print("   config:", PG["config"])
print("   fields per rank:", paper_gamma_audit["fields_recorded_per_rank"])
print("   per-batch values archived:", paper_gamma_audit["has_per_batch_values"])
print("   ->", paper_gamma_audit["conclusion"][:120])

print("\n" + "=" * 78)
print("B. CROSS-BATCH STATISTICS (6 disjoint 16-image batches, 96 samples)")
print("   %-12s %14s %12s %22s %8s" % ("block", "mean", "sd", "95% CI (t, n=6)", "CV%"))
for b in BLOCKS:
    v = per_block[b]
    print("   %-12s %14.3f %12.3f  [%10.3f,%10.3f] %8s"
          % (b, v["cross_batch_mean"], v["cross_batch_sd"] or 0,
             v["cross_batch_ci95"][0], v["cross_batch_ci95"][1],
             ("%.1f" % v["cross_batch_cv_pct"]) if v["cross_batch_cv_pct"] is not None else "-"))
print("   most unstable block (by relative sd):", worst)

print("\n" + "=" * 78)
print("C. SENSITIVITY TO REFERENCE-BATCH SIZE / CHOICE")
print("   %-12s %6s %8s %10s %-34s %10s" % ("cell", "eff.n", "topfreq", "n_orders", "top order", "alloc freq"))
for k, v in size_sens.items():
    print("   %-12s %6d %8.3f %10d %-34s %10.3f"
          % (k, v["n_effective_samples"], v["top_order_freq"], v["n_distinct_orders"],
             ",".join(v["top_order"])[:34], v["top_alloc_freq"]))

print("\n" + "=" * 78)
print("D. LEAVE-ONE-BATCH-OUT")
print("   order identical in %d/%d holdouts; max |vis| shift %.1f%%"
      % (lobo_summary["n_order_identical"], lobo_summary["n_holdouts"],
         lobo_summary["max_abs_vis_shift_pct"]))
print("   distinct raw allocation vectors across holdouts:", lobo_summary["alloc_raw_distinct"])
print("   per-block rank spread across holdouts:", lobo_summary["alloc_raw_max_spread"])

print("\n" + "=" * 78)
print("E. SAMPLES NEEDED FOR A TARGET CI WIDTH (per block)")
for b, v in n_req.items():
    if v:
        print("   %-12s rel.sd=%6.1f%%  n for 10%% CI=%6s  n for 5%% CI=%6s"
              % (b, v["relative_sd_pct"] or 0, v["n_for_10pct_ci"], v["n_for_5pct_ci"]))
print("\n" + "=" * 78)
print("F. ERROR BARS THE PAPER'S 5-PROMPT TABLE WOULD CARRY (projected)")
print("   %-6s %-12s %14s %18s %s" % ("rank", "block", "Gamma (published)", "projected 95% CI", "excl. 0"))
for rk in sorted(paper_gamma_se, key=lambda x: int(x[1:])):
    for b, v in paper_gamma_se[rk].items():
        if v["ci95_5_prompt"] is None:
            continue
        print("   %-6s %-12s %14.1f  [%11.1f,%11.1f]  %s"
              % (rk, b, v["gamma"], v["ci95_5_prompt"][0], v["ci95_5_prompt"][1],
                 v["ci_excludes_zero"]))
print("   blocks whose projected CI would include zero: %d"
      % len(paper_gamma_uncertainty["sign_risks"]))
print("   -> ", [(r["rank"], r["block"], round(r["gamma"], 1))
                 for r in paper_gamma_uncertainty["sign_risks"]])

print("\nwrote", dst)

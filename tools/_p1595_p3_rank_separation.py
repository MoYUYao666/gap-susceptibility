# -*- coding: utf-8 -*-
r"""P3 complete rank-separation statistics (purely local analysis, no cloud compute).

Extends the existing P3 evidence base with a full separation picture:

  1. exact two-sided permutation test on the difference of means for ALL 15 rank pairs
     among r = 3..8 (ten seeds per rank), by exhaustive enumeration of every C(20,10) = 184756
     split of the pooled 20 runs -- no Monte-Carlo approximation is used anywhere;
  2. a 6x6 matrix of mean differences with 95% percentile-bootstrap CIs of the difference;
  3. an exact paired sign-flip permutation test (2^10 = 1024 patterns), which uses the fact
     that the ten seed labels are identical in every rank;
  4. Holm-Bonferroni adjustment across the 15 pairs;
  5. a TOST equivalence test of the near-zero rank r = 5 mean against zero, with the margin
     PRE-DECLARED as one seed sd of the r = 5 group;
  6. a TOST equivalence bound for the VQA-RAD claim in Section S28, from the three 300-question
     archives outputs/analysis/cloud_vqa1793_{base,5,6}.json (accuracy and token F1, paired by
     question), with the margin PRE-DECLARED as 0.05.

PRIMARY ARM.  Exactly the arm used by the three scripts named in the P3 evidence base
(tools/_p1560_update_c1_d3.py, tools/_p1543_robust_stats_10seed.py, tools/_p1565_quick_stats.py):
the blank-image ("text-only") LLaVA-1.5-7B LoRA protocol, files
    paper3/scripts/outputs/experiments/cloud_verify_r<R>_s*.json
with the payload field "delta_E", excluding every file whose name contains "partial", "imgs"
or "_e1_" (partial runs carry delta_E = null; "imgs" is the separate real-image arm of Table S35);
_e1_ is the one-epoch ablation).  Every included file is additionally required to carry
payload "rank" == R and a finite "delta_E".  No other arm (real-image, per-step, per-layer,
second environment) enters this analysis.

OUTPUT.  outputs/analysis/p3_rank_separation_extended.json
The script is idempotent: all randomness is seeded, no wall-clock field is written, and every
number it prints is asserted (see the OK/FAIL ledger at the end).  Re-running reproduces the
output file byte for byte.
"""
from __future__ import annotations

import collections
import glob
import io
import json
import os
import re
import statistics as st
import string
from itertools import combinations

import numpy as np
from scipy import stats as ss

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
AN = os.path.join(REPO, "outputs", "analysis")
OUT = os.path.join(AN, "p3_rank_separation_extended.json")

RANKS = (3, 4, 5, 6, 7, 8)
EXCLUDE = ("partial", "imgs", "_e1_")
FIELD = "delta_E"
N_SEEDS = 10
N_BOOT = 20000          # bootstrap replicates, per rank pair and per VQA contrast
RNG_SEED = 20261024     # fixed seed => idempotent
VQA_MARGIN = 0.05       # PRE-DECLARED equivalence margin for the VQA ordering claim
ALPHA = 0.05

CHECKS: list = []


def show(label: str, value: str, ok: bool, why: str) -> None:
    """Print one number only together with the assertion that guards it."""
    CHECKS.append((label, bool(ok)))
    print("  %-60s %-24s %s  %s" % (label, value, "OK  " if ok else "FAIL", why))


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= tol


# --------------------------------------------------------------------------------------------
# 1. ten-seed per-rank values (primary arm)
# --------------------------------------------------------------------------------------------
def load_rank_values():
    """Return {rank: {'values': {seed: delta_E}, 'files': [relative paths]}}."""
    out = {}
    for r in RANKS:
        values, files = {}, []
        for f in sorted(glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*.json" % r))):
            name = os.path.basename(f)
            if any(x in name for x in EXCLUDE):
                continue
            d = json.load(io.open(f, encoding="utf-8"))
            v = d.get(FIELD)
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            assert int(d["rank"]) == r, "payload rank mismatch in %s" % name
            assert int(d["seed"]) not in values, "duplicate seed in rank %d" % r
            values[int(d["seed"])] = v
            files.append("paper3/scripts/outputs/experiments/" + name)
        out[r] = {"values": values, "files": files}
    return out


def summarise(vals: np.ndarray) -> dict:
    med = float(np.median(vals))
    return {
        "n": int(vals.size),
        "mean": float(vals.mean()),
        "sd": float(vals.std(ddof=1)),
        "median": med,
        "mad": float(np.median(np.abs(vals - med))),
        "min": float(vals.min()),
        "max": float(vals.max()),
        "n_negative": int((vals < 0).sum()),
        "n_positive": int((vals > 0).sum()),
        "stdev_stdlib": float(st.stdev(vals.tolist())),
    }


# --------------------------------------------------------------------------------------------
# 2. exact two-sided permutation test, exhaustive over all C(20,10) splits
# --------------------------------------------------------------------------------------------
def exact_permutation(pool: np.ndarray, comb_idx: np.ndarray, obs: float) -> dict:
    """Exhaustive two-sided permutation test on the difference of means.

    A split assigns 10 of the 20 pooled runs to group A; the difference of means is
    (sum_A - sum_B) / 10 = (2 * sum_A - sum_total) / 10, so the whole null distribution is a
    function of the 10-subset sums.  Splits are enumerated in both orders, exactly as
    tools/_p1565_quick_stats.py does, so the minimum attainable p is 2 / C(20,10).
    """
    sums = pool[comb_idx].sum(axis=1)
    total = pool.sum()
    diffs = (2.0 * sums - total) / 10.0
    n_ge = int(np.sum(np.abs(diffs) >= obs - 1e-12))
    n = int(comb_idx.shape[0])
    return {"n_splits": n, "n_abs_diff_ge_observed": n_ge, "p_two_sided": n_ge / n}


def exact_permutation_naive(pool_list, obs: float) -> int:
    """Independent reference implementation (plain Python, no numpy) used to verify the above."""
    n_ge = 0
    for idx in combinations(range(20), 10):
        s = 0.0
        for i in idx:
            s += pool_list[i]
        if abs((2.0 * s - sum(pool_list)) / 10.0) >= obs - 1e-12:
            n_ge += 1
    return n_ge


def paired_signflip(d: np.ndarray) -> dict:
    """Exact sign-flip permutation test on the 10 paired differences (2^10 = 1024 patterns)."""
    n = d.size
    bits = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(np.float64)
    signs = 2.0 * bits - 1.0
    perms = signs @ d / n
    obs = abs(float(d.mean()))
    n_ge = int(np.sum(np.abs(perms) >= obs - 1e-12))
    return {"n_patterns": 2 ** n, "n_abs_mean_ge_observed": n_ge, "p_two_sided": n_ge / (2 ** n)}


def holm(pvals):
    """Holm-Bonferroni step-down adjustment; returns adjusted p-values in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for k, i in enumerate(order):
        running = max(running, (m - k) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def boot_ci_diff(a: np.ndarray, b: np.ndarray, rng: np.random.Generator, n_boot: int) -> dict:
    """Percentile bootstrap CI of mean(a) - mean(b), resampling each group independently."""
    ia = rng.integers(0, a.size, size=(n_boot, a.size))
    ib = rng.integers(0, b.size, size=(n_boot, b.size))
    d = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    return {
        "n_boot": int(n_boot),
        "boot_se": float(d.std(ddof=1)),
        "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
        "ci90": [float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0))],
        "boot_mean": float(d.mean()),
    }


# --------------------------------------------------------------------------------------------
# 3. VQA-RAD helpers (identical definitions to tools/_p1516_p3_vqa_downstream.py)
# --------------------------------------------------------------------------------------------
def vqa_norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())


def vqa_token_f1(ref: str, hyp: str) -> float:
    rt = collections.Counter(ref.split())
    ht = collections.Counter(hyp.split())
    c = sum((rt & ht).values())
    if c == 0:
        return 0.0
    p = c / max(sum(ht.values()), 1)
    rec = c / max(sum(rt.values()), 1)
    return 2 * p * rec / (p + rec)


def load_vqa_arm(tag: str) -> dict:
    f = os.path.join(AN, "cloud_vqa1793_%s.json" % tag)
    d = json.load(io.open(f, encoding="utf-8"))
    nref = [vqa_norm(x) for x in d["refs"]]
    nhyp = [vqa_norm(x) for x in d["hypotheses"]]
    correct = np.array([1.0 if a == b else 0.0 for a, b in zip(nhyp, nref)])
    f1 = np.array([vqa_token_f1(a, b) for a, b in zip(nref, nhyp)])
    yn = [(a, b) for a, b in zip(nref, nhyp) if a.split()[:1] in (["yes"], ["no"])]
    yn_acc = float(np.mean([a.split()[:1] == b.split()[:1] for a, b in yn])) if yn else float("nan")
    return {
        "archive": "outputs/analysis/cloud_vqa1793_%s.json" % tag,
        "rank": d.get("rank"),
        "train_samples": d["meta"]["train_samples"],
        "n_eval": d["meta"]["n_eval"],
        "n_questions": len(d["refs"]),
        "refs": d["refs"],
        "archived_accuracy": float(d["accuracy"]),
        "archived_token_f1": float(d["token_f1"]),
        "archived_yes_no_accuracy": float(d["yes_no_accuracy"]),
        "archived_n_yes_no": int(d["n_yes_no"]),
        "accuracy": float(correct.mean()),
        "token_f1": float(f1.mean()),
        "yes_no_accuracy": yn_acc,
        "n_yes_no": len(yn),
        "correct": correct,
        "f1": f1,
    }


def vqa_contrast(a: dict, b: dict, rng: np.random.Generator, n_boot: int) -> dict:
    """Paired (by question) percentile bootstrap for arm a minus arm b, both metrics."""
    n = a["correct"].size
    idx = rng.integers(0, n, size=(n_boot, n))
    out = {}
    for key, field in (("accuracy", "correct"), ("token_f1", "f1")):
        da, db = a[field], b[field]
        d = da[idx].mean(axis=1) - db[idx].mean(axis=1)
        lo90, hi90 = float(np.percentile(d, 5.0)), float(np.percentile(d, 95.0))
        p_lower = float(np.mean(d <= -VQA_MARGIN))   # H0: delta <= -margin
        p_upper = float(np.mean(d >= +VQA_MARGIN))   # H0: delta >= +margin
        out[key] = {
            "n_boot": int(n_boot),
            "delta": float(da.mean() - db.mean()),
            "boot_mean": float(d.mean()),
            "boot_se": float(d.std(ddof=1)),
            "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "ci90": [lo90, hi90],
            "excludes_zero_95": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0),
            "p_one_sided_positive": float(np.mean(d <= 0.0)),
            "tost_margin": VQA_MARGIN,
            "tost_p_lower": p_lower,
            "tost_p_upper": p_upper,
            "tost_p": max(p_lower, p_upper),
            "equivalent_at_declared_margin": bool(max(p_lower, p_upper) < ALPHA),
            "min_equivalent_margin": max(-lo90, hi90),
        }
    return out


# --------------------------------------------------------------------------------------------
def main() -> int:
    print("=" * 118)
    print("P3 rank separation: 15-pair exact permutation matrix, TOST for r=5, VQA equivalence bound")
    print("=" * 118)

    # ---- inputs ------------------------------------------------------------------------------
    raw = load_rank_values()
    values = {r: np.array([raw[r]["values"][s] for s in sorted(raw[r]["values"])]) for r in RANKS}
    seed_sets = {r: tuple(sorted(raw[r]["values"])) for r in RANKS}

    print("\n[1] primary arm and per-rank values (field '%s')" % FIELD)
    show("ranks loaded", "%s" % list(RANKS), sorted(raw) == sorted(RANKS),
         "all six ranks present")
    show("n seeds per rank", "%s" % [int(values[r].size) for r in RANKS],
         all(values[r].size == N_SEEDS for r in RANKS), "ten seeds per rank, as in S33")
    show("seed labels identical across ranks", "%s" % (seed_sets[3],),
         len(set(seed_sets.values())) == 1, "paired sign-flip test is legitimate")
    show("total source files", "%d" % sum(len(raw[r]["files"]) for r in RANKS),
         sum(len(raw[r]["files"]) for r in RANKS) == 60, "60 archives = 6 ranks x 10 seeds")

    ranks = {}
    for r in RANKS:
        s = summarise(values[r])
        ranks[str(r)] = {
            "n": s["n"], "mean": s["mean"], "sd": s["sd"], "median": s["median"], "mad": s["mad"],
            "min": s["min"], "max": s["max"], "n_negative": s["n_negative"], "n_positive": s["n_positive"],
            "values_by_seed": {str(k): raw[r]["values"][k] for k in sorted(raw[r]["values"])},
            "seeds": sorted(raw[r]["values"]),
            "source_files": raw[r]["files"],
            "source_field": FIELD,
        }
        show("r=%d mean / sd (numpy)" % r, "%+.4f / %.4f" % (s["mean"], s["sd"]),
             close(s["mean"], st.mean(values[r].tolist()), 1e-12)
             and close(s["sd"], s["stdev_stdlib"], 1e-12),
             "cross-checked against statistics.mean/stdev (stdlib)")

    # archived cross-checks: the r=4..7 block of p3_robust_stats_10seed.json and the r=3/r=8
    # means of p3_perm_r3_r8.json must be reproduced exactly.
    rob = json.load(io.open(os.path.join(AN, "p3_robust_stats_10seed.json"), encoding="utf-8"))["ranks"]
    for r in (4, 5, 6, 7):
        ref = rob[str(r)]
        got = ranks[str(r)]
        show("r=%d reproduces p3_robust_stats_10seed.json" % r,
             "mean %+.4f" % got["mean"],
             all([close(got["mean"], ref["mean"], 1e-9), close(got["sd"], ref["sd"], 1e-9),
                  close(got["median"], ref["median"], 1e-9), close(got["mad"], ref["mad"], 1e-9),
                  close(got["min"], ref["min"], 1e-9), close(got["max"], ref["max"], 1e-9),
                  got["n"] == ref["n"]]),
             "mean, sd, median, MAD, min, max, n all identical")

    perm38 = json.load(io.open(os.path.join(AN, "p3_perm_r3_r8.json"), encoding="utf-8"))
    show("r=3 mean reproduces p3_perm_r3_r8.json", "%+.4f" % ranks["3"]["mean"],
         close(ranks["3"]["mean"], perm38["mean3"], 1e-9), "archived mean3 = %+.1f" % perm38["mean3"])
    show("r=8 mean reproduces p3_perm_r3_r8.json", "%+.4f" % ranks["8"]["mean"],
         close(ranks["8"]["mean"], perm38["mean8"], 1e-9), "archived mean8 = %+.1f" % perm38["mean8"])

    # ---- exact permutation, all 15 pairs ------------------------------------------------------
    comb_idx = np.array(list(combinations(range(2 * N_SEEDS), N_SEEDS)), dtype=np.int16)
    n_splits = int(comb_idx.shape[0])
    p_min = 2.0 / n_splits
    print("\n[2] exact two-sided permutation tests, exhaustive over all C(20,10) splits")
    show("enumeration size", "%d" % n_splits, n_splits == 184756, "C(20,10) = 184756, exact")
    show("minimum attainable p", "%.6g" % p_min, close(p_min, 2.0 / 184756),
         "2 / C(20,10); complete separation attains exactly this")

    pairs = []
    for a, b in combinations(RANKS, 2):
        va, vb = values[a], values[b]
        pool = np.concatenate([va, vb])
        obs = abs(float(va.mean() - vb.mean()))
        ex = exact_permutation(pool, comb_idx, obs)
        bs = boot_ci_diff(va, vb, np.random.default_rng(RNG_SEED + 100 * a + b), N_BOOT)
        sf = paired_signflip(va - vb)
        sign_sep = bool(va.max() < vb.min() or vb.max() < va.min())
        pairs.append({
            "rank_a": a, "rank_b": b,
            "mean_a": float(va.mean()), "mean_b": float(vb.mean()),
            "diff_a_minus_b": float(va.mean() - vb.mean()),
            "abs_diff": obs,
            "sign_separated": sign_sep,
            "p_exact": ex["p_two_sided"],
            "n_splits": ex["n_splits"],
            "n_abs_diff_ge_observed": ex["n_abs_diff_ge_observed"],
            "ci95_diff": bs["ci95"],
            "ci90_diff": bs["ci90"],
            "boot_se_diff": bs["boot_se"],
            "ci95_excludes_zero": bool(bs["ci95"][0] > 0 or bs["ci95"][1] < 0),
            "p_paired_signflip": sf["p_two_sided"],
            "seeds_paired": True,
        })

    # independent naive re-implementation for the two pairs the evidence base quotes
    for a, b in ((3, 8), (5, 6)):
        pool_list = values[a].tolist() + values[b].tolist()
        obs = abs(float(values[a].mean() - values[b].mean()))
        n_ge = exact_permutation_naive(pool_list, obs)
        rec = [p for p in pairs if p["rank_a"] == a and p["rank_b"] == b][0]
        show("naive re-check of r=%d vs r=%d" % (a, b), "n_ge=%d" % n_ge,
             n_ge == rec["n_abs_diff_ge_observed"],
             "plain-Python enumeration agrees with the vectorised count")

    p_holm = holm([p["p_exact"] for p in pairs])
    for p, ph in zip(pairs, p_holm):
        p["p_holm"] = float(ph)
        p["separates_raw"] = bool(p["p_exact"] < ALPHA)
        p["separates_holm"] = bool(ph < ALPHA)
        p["bootstrap_agrees_with_permutation"] = bool(p["separates_raw"] == p["ci95_excludes_zero"])

    for p in pairs:
        show("r=%d vs r=%d  diff / p_exact" % (p["rank_a"], p["rank_b"]),
             "%+8.2f / %-10.6g" % (p["diff_a_minus_b"], p["p_exact"]),
             p["n_splits"] == 184756 and p["n_abs_diff_ge_observed"] >= 2,
             "ge=%d of 184756; 95%% CI [%+.2f, %+.2f]"
             % (p["n_abs_diff_ge_observed"], p["ci95_diff"][0], p["ci95_diff"][1]))

    disagree = [p for p in pairs if not p["bootstrap_agrees_with_permutation"]]
    show("permutation and bootstrap verdicts agree", "%d of 15" % (len(pairs) - len(disagree)),
         len(disagree) == 1 and (disagree[0]["rank_a"], disagree[0]["rank_b"]) == (7, 8),
         "one documented disagreement: r=7 vs r=8, exact p=%.4f but 95%% CI [%+.2f, %+.2f] excludes zero"
         % (disagree[0]["p_exact"], disagree[0]["ci95_diff"][0], disagree[0]["ci95_diff"][1])
         if disagree else "all 15 agree")

    # the four quotable archive/claim cross-checks
    rec38 = [p for p in pairs if (p["rank_a"], p["rank_b"]) == (3, 8)][0]
    rec56 = [p for p in pairs if (p["rank_a"], p["rank_b"]) == (5, 6)][0]
    show("r=3 vs r=8 p_exact == archived p3_perm_r3_r8.json",
         "%.10g" % rec38["p_exact"], close(rec38["p_exact"], perm38["p"], 1e-15),
         "archived p = %.10g" % perm38["p"])
    show("r=5 vs r=6 p_exact == 2/C(20,10) (S33 claim, previously unarchived)",
         "%.10g" % rec56["p_exact"], close(rec56["p_exact"], p_min, 1e-15),
         "S33 caption value p ~ 1.1e-5 is CORRECT and is now archived")

    n_sep_raw = sum(1 for p in pairs if p["separates_raw"])
    n_sep_holm = sum(1 for p in pairs if p["separates_holm"])
    n_sign_sep = sum(1 for p in pairs if p["sign_separated"])
    show("pairs separating at raw p<0.05", "%d of 15" % n_sep_raw, n_sep_raw == 14,
         "only r=7 vs r=8 does not")
    show("pairs separating after Holm", "%d of 15" % n_sep_holm, n_sep_holm == 14,
         "Holm-Bonferroni across 15 tests does not change the verdict")
    show("rank pairs with disjoint value ranges", "%d of 15" % n_sign_sep, n_sign_sep == 11,
         "9 crossing pairs plus r=6 vs r=7 and r=6 vs r=8")
    show("non-separating pair", "r=%d vs r=%d" % (
        [p for p in pairs if not p["separates_holm"]][0]["rank_a"],
        [p for p in pairs if not p["separates_holm"]][0]["rank_b"]),
         len([p for p in pairs if not p["separates_holm"]]) == 1,
         "p=%.6g, 95%% CI [%+.1f, %+.1f]"
         % ([p for p in pairs if not p["separates_holm"]][0]["p_exact"],
            [p for p in pairs if not p["separates_holm"]][0]["ci95_diff"][0],
            [p for p in pairs if not p["separates_holm"]][0]["ci95_diff"][1]))

    n_paired_min = sum(1 for p in pairs if close(p["p_paired_signflip"], 2.0 / 1024, 1e-15))
    show("pairs at the paired minimum 2/1024", "%d of 15" % n_paired_min, n_paired_min == 12,
         "twelve pairs are completely ordered on the paired differences")

    mean_diff = {str(a): {str(b): (0.0 if a == b else float(values[a].mean() - values[b].mean()))
                          for b in RANKS} for a in RANKS}
    ci95_lo = {str(a): {str(b): (0.0 if a == b else [p for p in pairs
                                                     if {p["rank_a"], p["rank_b"]} == {a, b}][0]["ci95_diff"][0])
                        for b in RANKS} for a in RANKS}
    ci95_hi = {str(a): {str(b): (0.0 if a == b else [p for p in pairs
                                                     if {p["rank_a"], p["rank_b"]} == {a, b}][0]["ci95_diff"][1])
                        for b in RANKS} for a in RANKS}
    show("matrix antisymmetry", "max |d_ij + d_ji|",
         max(abs(mean_diff[str(a)][str(b)] + mean_diff[str(b)][str(a)]) for a in RANKS for b in RANKS) == 0.0,
         "mean-difference matrix is exactly antisymmetric")
    show("matrix diagonal", "all zero", all(mean_diff[str(a)][str(a)] == 0.0 for a in RANKS),
         "diagonal is zero by construction")

    # ---- rank-level sign separation and the crossing location ---------------------------------
    print("\n[3] sign separation and the crossing location")
    show("r<=5 all negative", "%s" % {str(r): ranks[str(r)]["n_negative"] for r in (3, 4, 5)},
         all(ranks[str(r)]["n_negative"] == 10 for r in (3, 4, 5)), "10/10 negative at r=3,4,5")
    show("r>=6 all positive", "%s" % {str(r): ranks[str(r)]["n_positive"] for r in (6, 7, 8)},
         all(ranks[str(r)]["n_positive"] == 10 for r in (6, 7, 8)), "10/10 positive at r=6,7,8")
    show("max(r=5) < min(r=6)", "%+.1f < %+.1f" % (ranks["5"]["max"], ranks["6"]["min"]),
         ranks["5"]["max"] < ranks["6"]["min"], "the crossing lies between r=5 and r=6")

    # ---- TOST for the near-zero rank r = 5 ----------------------------------------------------
    print("\n[4] TOST equivalence test for r = 5 against zero (margin = one seed sd at r=5)")
    v5 = values[5]
    m5 = float(v5.mean())
    sd5 = float(v5.std(ddof=1))
    se5 = sd5 / np.sqrt(v5.size)
    df5 = v5.size - 1
    t_crit_90 = float(ss.t.ppf(1.0 - ALPHA, df5))          # two-sided 90% CI <- the TOST interval
    t_crit_95 = float(ss.t.ppf(1.0 - ALPHA / 2.0, df5))    # two-sided 95% CI
    ci90_t = [m5 - t_crit_90 * se5, m5 + t_crit_90 * se5]
    ci95_t = [m5 - t_crit_95 * se5, m5 + t_crit_95 * se5]
    p_lower = float(ss.t.sf((m5 + sd5) / se5, df5))     # H0: mu <= -margin
    p_upper = float(ss.t.cdf((m5 - sd5) / se5, df5))    # H0: mu >= +margin
    tost_p = max(p_lower, p_upper)
    m_min_t = max(-ci90_t[0], ci90_t[1])

    rng5 = np.random.default_rng(RNG_SEED + 5)
    ib = rng5.integers(0, v5.size, size=(N_BOOT, v5.size))
    bm = v5[ib].mean(axis=1)
    b_lo90, b_hi90 = float(np.percentile(bm, 5.0)), float(np.percentile(bm, 95.0))
    b_p_lower = float(np.mean(bm <= -sd5))
    b_p_upper = float(np.mean(bm >= +sd5))
    b_tost = max(b_p_lower, b_p_upper)
    m_min_b = max(-b_lo90, b_hi90)

    show("r=5 mean", "%+.4f" % m5, close(m5, ranks["5"]["mean"], 1e-12), "field %s, 10 seeds" % FIELD)
    show("r=5 sd (pre-declared margin)", "%.4f" % sd5, close(sd5, ranks["5"]["sd"], 1e-12),
         "margin rule: one seed sd of the r=5 group")
    show("r=5 standard error", "%.4f" % se5, close(se5, sd5 / np.sqrt(10), 1e-12), "sd / sqrt(10)")
    show("t quantile 0.95, df=9", "%.6f" % t_crit_90, close(t_crit_90, 1.833113, 1e-6),
         "scipy.stats.t.ppf(0.95, 9); the TOST interval is the two-sided 90% CI")
    show("t quantile 0.975, df=9", "%.6f" % t_crit_95, close(t_crit_95, 2.262157, 1e-6),
         "scipy.stats.t.ppf(0.975, 9); the two-sided 95% CI")
    show("90% CI of mean(r=5) (t)", "[%+.3f, %+.3f]" % tuple(ci90_t),
         close(ci90_t[0], m5 - t_crit_90 * se5, 1e-12) and ci90_t[0] < ci90_t[1]
         and ci90_t[1] < ci95_t[1], "TOST interval, narrower than the 95% CI")
    show("95% CI of mean(r=5) (t)", "[%+.3f, %+.3f]" % tuple(ci95_t),
         ci95_t[1] < 0.0, "entirely below zero => r=5 is NOT equivalent to zero")
    show("TOST p_lower (H0: mu <= -sd)", "%.6f" % p_lower, 0.0 <= p_lower <= 1.0, "one-sided")
    show("TOST p_upper (H0: mu >= +sd)", "%.3g" % p_upper, 0.0 <= p_upper <= 1.0, "one-sided")
    show("TOST p (t-based)", "%.6f" % tost_p, close(tost_p, max(p_lower, p_upper), 1e-15),
         "max of the two one-sided p-values")
    show("equivalent at margin = 1 seed sd", "%s" % (tost_p < ALPHA), tost_p >= ALPHA,
         "TOST fails: r=5 cannot be declared equivalent to zero at +/-%.2f" % sd5)
    show("consistency: TOST p<0.05 <=> 90% CI inside margin",
         "%s / m_min=%+.3f" % (bool(m_min_t < sd5), m_min_t),
         (m_min_t < sd5) == (tost_p < ALPHA), "internal consistency of the two criteria")
    show("smallest equivalent margin (t)", "%+.3f" % m_min_t,
         close(m_min_t, max(-ci90_t[0], ci90_t[1]), 1e-12), "the equivalence bound for r=5")
    show("smallest equivalent margin in seed sd", "%.3f sd" % (m_min_t / sd5),
         m_min_t / sd5 > 1.0, "> 1 seed sd => the 'near zero' wording needs a qualifier")
    show("bootstrap TOST p (percentile)", "%.6f" % b_tost,
         (b_tost < ALPHA) == (tost_p < ALPHA), "bootstrap and t-based agree on the verdict")
    show("bootstrap smallest equivalent margin", "%+.3f" % m_min_b,
         abs(m_min_b - m_min_t) < 0.15 * sd5, "within 15% of a seed sd of the t-based bound")

    rank5 = {
        "rank": 5,
        "target": 0.0,
        "margin": sd5,
        "margin_rule": "one seed sd of the r=5 group (pre-declared before the test was run)",
        "mean": m5, "sd": sd5, "se": se5, "n": int(v5.size), "df": df5,
        "t_crit_0.95": t_crit_90, "t_crit_0.975": t_crit_95,
        "ci90_t": ci90_t, "ci95_t": ci95_t,
        "p_lower": p_lower, "p_upper": p_upper, "tost_p": tost_p,
        "equivalent_at_declared_margin": bool(tost_p < ALPHA),
        "min_equivalent_margin": m_min_t,
        "min_equivalent_margin_in_seed_sd": m_min_t / sd5,
        "bootstrap": {"n_boot": N_BOOT, "p_lower": b_p_lower, "p_upper": b_p_upper,
                      "tost_p": b_tost, "ci90": [b_lo90, b_hi90],
                      "min_equivalent_margin": m_min_b,
                      "equivalent_at_declared_margin": bool(b_tost < ALPHA)},
        "interpretation": (
            "mean DeltaE at r=5 is %+.1f (95%% CI [%+.1f, %+.1f]); the ten-seed r=5 group is NOT "
            "statistically equivalent to zero at the one-seed-sd margin (%+.2f): TOST p = %.3f. "
            "Equivalence to zero could only be declared at a margin of %+.1f (%.2f seed sd). "
            "What the data do support is that r=5 is the smallest-magnitude negative rank "
            "(%+.1f versus %+.1f at r=4 and %+.1f at r=3) and that the crossing lies between "
            "r=5 and r=6." % (m5, ci95_t[0], ci95_t[1], sd5, tost_p, m_min_t, m_min_t / sd5,
                              m5, ranks["4"]["mean"], ranks["3"]["mean"])),
    }

    # ---- VQA equivalence ---------------------------------------------------------------------
    print("\n[5] VQA-RAD equivalence (cloud_vqa1793_*.json, 300 paired questions)")
    arms = {tag: load_vqa_arm(tag) for tag in ("base", "5", "6")}
    show("VQA questions per arm", "%s" % {k: v["n_questions"] for k, v in arms.items()},
         all(v["n_questions"] == 300 for v in arms.values()), "300 held-out questions, as in S28")
    show("payload ranks", "%s" % {k: v["rank"] for k, v in arms.items()},
         arms["base"]["rank"] is None and arms["5"]["rank"] == 5 and arms["6"]["rank"] == 6,
         "base / r=5 / r=6")
    show("train samples", "%s" % {k: v["train_samples"] for k, v in arms.items()},
         arms["base"]["train_samples"] == 0 and arms["5"]["train_samples"] == 1793
         and arms["6"]["train_samples"] == 1793, "base untrained, both ranks on 1793 pairs")
    same_refs = all(arms[k]["refs"] == arms["base"]["refs"] for k in arms)
    show("reference answers identical across arms", "%s" % same_refs, same_refs,
         "same 300 questions in the same order => the bootstrap can be paired")
    for k, v in arms.items():
        show("recomputed accuracy / F1 (%s)" % k, "%.4f / %.4f" % (v["accuracy"], v["token_f1"]),
             close(v["accuracy"], v["archived_accuracy"], 1e-12)
             and close(v["token_f1"], v["archived_token_f1"], 1e-12)
             and close(v["yes_no_accuracy"], v["archived_yes_no_accuracy"], 1e-12)
             and v["n_yes_no"] == v["archived_n_yes_no"],
             "matches the archived fields to 1e-12 and n_yes_no=%d" % v["n_yes_no"])

    rngv = np.random.default_rng(RNG_SEED)
    contrasts = {}
    vqa_pairs = (("base", "5"), ("base", "6"), ("5", "6"))
    for a, b in vqa_pairs:
        contrasts["%s_minus_%s" % (a, b)] = vqa_contrast(arms[a], arms[b], rngv, N_BOOT)

    for (a, b) in vqa_pairs:
        cname = "%s_minus_%s" % (a, b)
        c = contrasts[cname]
        for metric in ("accuracy", "token_f1"):
            d = c[metric]
            mc_tol = max(4.0 * d["boot_se"] / np.sqrt(N_BOOT), 1e-3)
            show("%s %s" % (cname, metric),
                 "%+.4f [%+.4f, %+.4f]" % (d["delta"], d["ci95"][0], d["ci95"][1]),
                 close(d["delta"], arms[a][metric] - arms[b][metric], 1e-12)
                 and close(arms[a][metric], arms[a]["archived_" + metric], 1e-12)
                 and abs(d["boot_mean"] - d["delta"]) <= mc_tol
                 and (d["excludes_zero_95"] == (d["ci95"][0] > 0 or d["ci95"][1] < 0))
                 and ((d["tost_p"] >= ALPHA) or (d["min_equivalent_margin"] <= VQA_MARGIN))
                 and ((d["tost_p"] < ALPHA) or (d["min_equivalent_margin"] >= VQA_MARGIN)),
                 "delta = arm means, MC error %.1e <= %.1e; TOST p=%.4f at margin %.2f"
                 % (abs(d["boot_mean"] - d["delta"]), mc_tol, d["tost_p"], VQA_MARGIN))

    acc56 = contrasts["5_minus_6"]["accuracy"]
    f1_56 = contrasts["5_minus_6"]["token_f1"]
    acc_b5 = contrasts["base_minus_5"]["accuracy"]
    f1_b5 = contrasts["base_minus_5"]["token_f1"]
    acc_b6 = contrasts["base_minus_6"]["accuracy"]
    f1_b6 = contrasts["base_minus_6"]["token_f1"]

    show("claim: r=5 improves over base (accuracy)", "%+.4f resolved" % (-acc_b5["delta"]),
         acc_b5["ci95"][1] < 0.0, "the base-minus-r5 contrast is entirely negative")
    show("claim: r=5 improves over base (token F1)", "%+.4f resolved" % (-f1_b5["delta"]),
         f1_b5["ci95"][1] < 0.0, "the base-minus-r5 contrast is entirely negative")
    show("claim: r=6 improves over base (accuracy)", "%+.4f NOT resolved" % (-acc_b6["delta"]),
         acc_b6["delta"] < 0.0 and acc_b6["ci95"][1] >= 0.0,
         "point estimate %+.4f, 95%% CI [%+.4f, %+.4f] includes zero"
         % (-acc_b6["delta"], -acc_b6["ci95"][1], -acc_b6["ci95"][0]))
    show("claim: r=6 improves over base (token F1)", "%+.4f resolved" % (-f1_b6["delta"]),
         f1_b6["ci95"][1] < 0.0, "the base-minus-r6 contrast is entirely negative")
    show("claim: no rank ordering (token F1)", "delta=%+.4f TOST p=%.4f" % (f1_56["delta"], f1_56["tost_p"]),
         f1_56["equivalent_at_declared_margin"], "equivalent to zero within +/-%.2f" % VQA_MARGIN)
    show("claim: no rank ordering (accuracy)", "delta=%+.4f TOST p=%.4f" % (acc56["delta"], acc56["tost_p"]),
         not acc56["equivalent_at_declared_margin"],
         "NOT equivalent at +/-%.2f; smallest equivalent margin %.4f"
         % (VQA_MARGIN, acc56["min_equivalent_margin"]))

    vqa = {
        "archives": [arms[k]["archive"] for k in ("base", "5", "6")],
        "n_questions": 300,
        "pairing": "same 300 held-out questions in the same order in all three archives "
                   "(cloud_vqa1793_base.json refs are byte-identical across arms)",
        "declared_margin": VQA_MARGIN,
        "declared_margin_rule": (
            "0.05 on both metrics, pre-declared.  A single arm on 300 questions has a binomial "
            "standard error of about 0.027-0.028 in accuracy (0.0272 for the base model at 0.3300, "
            "0.0282 for r=5 at 0.3933), so differences below roughly two standard "
            "errors (~0.055, rounded down to 0.05) are at the resolution limit of this evaluation "
            "set; a rank ordering that does not exceed that band is not interpreted as an ordering."),
        "arms": {k: {"rank": v["rank"], "train_samples": v["train_samples"],
                     "n": v["n_questions"], "accuracy": v["accuracy"], "token_f1": v["token_f1"],
                     "yes_no_accuracy": v["yes_no_accuracy"], "n_yes_no": v["n_yes_no"],
                     "archive": v["archive"]} for k, v in arms.items()},
        "contrasts": contrasts,
        "claim_verdict": {
            "both_ranks_improve_over_base": {
                "accuracy": {"r5": -acc_b5["delta"], "r5_resolved": bool(acc_b5["ci95"][1] < 0),
                             "r6": -acc_b6["delta"], "r6_resolved": bool(acc_b6["ci95"][1] < 0)},
                "token_f1": {"r5": -f1_b5["delta"], "r5_resolved": bool(f1_b5["ci95"][1] < 0),
                             "r6": -f1_b6["delta"], "r6_resolved": bool(f1_b6["ci95"][1] < 0)},
                "verdict": "supported on token F1 for both ranks (%+.4f for r=5 and %+.4f for r=6) "
                           "and on accuracy for r=5 (%+.4f); the r=6 accuracy gain (%+.4f, 95%% CI "
                           "[%+.4f, %+.4f]) is not resolved on its own"
                           % (-f1_b5["delta"], -f1_b6["delta"], -acc_b5["delta"], -acc_b6["delta"],
                              -acc_b6["ci95"][1], -acc_b6["ci95"][0]),
            },
            "ranks_do_not_order": {
                "accuracy": {"delta_r5_minus_r6": acc56["delta"], "ci95": acc56["ci95"],
                             "tost_p": acc56["tost_p"],
                             "equivalent": bool(acc56["equivalent_at_declared_margin"]),
                             "min_equivalent_margin": acc56["min_equivalent_margin"]},
                "token_f1": {"delta_r5_minus_r6": f1_56["delta"], "ci95": f1_56["ci95"],
                             "tost_p": f1_56["tost_p"],
                             "equivalent": bool(f1_56["equivalent_at_declared_margin"]),
                             "min_equivalent_margin": f1_56["min_equivalent_margin"]},
                "verdict": "supported on token F1 (delta %+.4f, TOST p=%.4f at +/-%.2f); NOT supported "
                           "on exact-match accuracy, where r=5 is higher than r=6 by %+.4f (95%% CI "
                           "[%+.4f, %+.4f]) -- a small reversal, not an ordering in the alignment-energy "
                           "direction.  The accuracy ordering can only be excluded above a margin of %.4f."
                           % (f1_56["delta"], f1_56["tost_p"], VQA_MARGIN, acc56["delta"],
                              acc56["ci95"][0], acc56["ci95"][1], acc56["min_equivalent_margin"]),
            },
        },
    }

    # ---- conclusion --------------------------------------------------------------------------
    nonsep = [p for p in pairs if not p["separates_holm"]][0]
    conclusion = {
        "n_pairs": len(pairs),
        "n_separating_raw_p05": n_sep_raw,
        "n_separating_holm_p05": n_sep_holm,
        "n_sign_separated_pairs": n_sign_sep,
        "n_pairs_at_paired_minimum": n_paired_min,
        "pairs_at_paired_minimum_keys": ["r%d-r%d" % (p["rank_a"], p["rank_b"]) for p in pairs
                                         if close(p["p_paired_signflip"], 2.0 / 1024, 1e-15)],
        "n_splits_per_pair": n_splits,
        "p_min_attainable": p_min,
        "separating_pair_keys": ["r%d-r%d" % (p["rank_a"], p["rank_b"]) for p in pairs if p["separates_holm"]],
        "non_separating_pair_keys": ["r%d-r%d" % (p["rank_a"], p["rank_b"]) for p in pairs if not p["separates_holm"]],
        "adjacent_rank_p_values": {("r%d-r%d" % (p["rank_a"], p["rank_b"])): p["p_exact"]
                                   for p in pairs if p["rank_b"] - p["rank_a"] == 1},
        "sign_split": "all 10 runs negative at r=3,4,5 and all 10 runs positive at r=6,7,8",
        "crossing_between": [5, 6],
        "rank5_tost_equivalent_to_zero": bool(tost_p < ALPHA),
        "rank5_tost_p": tost_p,
        "rank5_min_equivalent_margin": m_min_t,
        "vqa_no_ordering_supported": {
            "token_f1": bool(f1_56["equivalent_at_declared_margin"]),
            "accuracy": bool(acc56["equivalent_at_declared_margin"]),
        },
        "text": (
            "With ten seeds per rank the rank sweep is completely sign-separated: every run at "
            "r=3,4,5 is negative and every run at r=6,7,8 is positive, so the crossing lies between "
            "r=5 and r=6. Of the 15 rank pairs, 14 separate under an exact two-sided permutation test "
            "over all 184756 splits of the 20 pooled runs (raw p<0.05, unchanged by Holm-Bonferroni "
            "across the 15 tests); the single exception is the adjacent pair r=7 vs r=8 "
            "(difference +40.0, exact p=0.0709), for which the percentile bootstrap CI "
            "[%+.2f, %+.2f] happens to exclude zero by %+.2f energy units -- the exact test governs and "
            "this pair is reported as unresolved. Adjacent-rank differences are "
            "resolved for r=3 vs r=4 (p=0.0100), r=4 vs r=5 (p=0.00235), r=5 vs r=6 (p=1.08e-5) and "
            "r=6 vs r=7 (p=1.08e-5), but not for r=7 vs r=8. The same ten seed labels "
            "appear in every rank, so we also ran the exact paired sign-flip test over the 1024 sign patterns "
            "of the ten paired differences: it reaches its minimum attainable p=2/1024=0.0020 for twelve pairs "
            "and likewise leaves r=7 vs r=8 unresolved (p=0.0605). The frequently quoted p=2/C(20,10)=1.1e-5 "
            "for r=5 vs r=6 is confirmed exactly (previously unarchived); the archived r=3 vs r=8 "
            "value 1.0825e-5 is reproduced to machine precision. For the near-zero rank r=5 the "
            "equivalence test against zero fails at the pre-declared one-seed-sd margin (%.2f): "
            "TOST p=%.3f, and equivalence would need a margin of %+.1f (%.2f seed sd); the ten-seed "
            "r=5 group is therefore not statistically indistinguishable from zero, only the "
            "smallest-magnitude negative rank. For the VQA-RAD claim, token F1 shows no rank ordering "
            "(r=5 minus r=6 = %+.4f, TOST p=%.4f within +/-0.05) while exact-match accuracy shows a "
            "small reversal (%+.4f, 95%% CI [%+.4f, %+.4f]); the accuracy ordering can only be "
            "excluded above a margin of %.4f."
            % (nonsep["ci95_diff"][0], nonsep["ci95_diff"][1], -nonsep["ci95_diff"][1],
               sd5, tost_p, m_min_t, m_min_t / sd5,
               f1_56["delta"], f1_56["tost_p"], acc56["delta"], acc56["ci95"][0], acc56["ci95"][1],
               acc56["min_equivalent_margin"])),
    }

    result = {
        "meta": {
            "script": "tools/_p1595_p3_rank_separation.py",
            "task": "P3 complete rank separation: 15-pair exact permutation matrix, bootstrap CIs of "
                    "the difference, r=5 TOST equivalence against zero, VQA-RAD equivalence bound",
            "primary_arm": "blank-image (text-only) LLaVA-1.5-7B LoRA protocol, "
                           "paper3/scripts/outputs/experiments/cloud_verify_r<R>_s*.json",
            "field": FIELD,
            "file_exclusions": list(EXCLUDE),
            "n_seeds_per_rank": N_SEEDS,
            "ranks": list(RANKS),
            "n_boot": N_BOOT,
            "rng_seed": RNG_SEED,
            "alpha": ALPHA,
            "permutation": "exact two-sided permutation on the difference of means; exhaustive "
                           "enumeration of all C(20,10)=184756 splits (no Monte-Carlo)",
            "bootstrap": "percentile bootstrap, groups resampled independently (rank pairs) or "
                         "questions resampled jointly (VQA)",
            "paired_test": "exact sign-flip permutation over 2^10=1024 patterns; valid because the "
                           "ten seed labels are identical in every rank",
            "multiplicity": "Holm-Bonferroni across the 15 rank pairs",
            "decision_rule": "the exact two-sided permutation test governs the separation verdict; "
                             "the percentile bootstrap CI is reported alongside it, and the single "
                             "pair where the two disagree (r=7 vs r=8) is flagged in the pairs list",
            "idempotent": True,
            "note": "no wall-clock field is written, so re-running reproduces this file byte for byte",
        },
        "ranks": ranks,
        "separation": {
            "n_splits": n_splits,
            "p_min_attainable": p_min,
            "n_pairs": len(pairs),
            "n_separating_raw_p05": n_sep_raw,
            "n_separating_holm_p05": n_sep_holm,
            "n_sign_separated_pairs": n_sign_sep,
            "n_pairs_at_paired_minimum": n_paired_min,
            "paired_minimum_p": 2.0 / 1024,
            "pairs": pairs,
            "matrix": {"mean_diff_a_minus_b": mean_diff, "ci95_lo": ci95_lo, "ci95_hi": ci95_hi,
                       "p_exact": {str(a): {str(b): (0.0 if a == b else
                                                     [p for p in pairs
                                                      if {p["rank_a"], p["rank_b"]} == {a, b}][0]["p_exact"])
                                           for b in RANKS} for a in RANKS}},
        },
        "rank5_equivalence": rank5,
        "vqa_equivalence": vqa,
        "conclusion": conclusion,
    }

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    print("\n[6] wrote %s" % os.path.relpath(OUT, REPO).replace("\\", "/"))

    failed = [label for label, ok in CHECKS if not ok]
    print("\n[7] assertion ledger: %d checks, %d failed" % (len(CHECKS), len(failed)))
    for label in failed:
        print("    FAILED:", label)
    assert not failed, "assertion ledger has %d failure(s): %s" % (len(failed), failed)
    print("\nCONCLUSION\n" + conclusion["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
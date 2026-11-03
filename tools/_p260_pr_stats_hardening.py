# -*- coding: utf-8 -*-
"""
PR statistics hardening — pseudo-replication and between-group confounding in the
DG -> R@1 relation.

WHY
    Pattern Recognition rejected the predecessor manuscript (PR-D-26-10149).  All
    three reviewers independently objected that the manuscript treats non-independent
    experiment runs as independent observations (pseudo-replication) and that the
    correlation is confounded between groups.  One reviewer's exact words:
    "Partial correlation controlling for CG alone does not resolve this issue".

    The manuscript reports  r = -0.714  for DG vs R@1  over n = 204 rows.

WHAT THIS SCRIPT DOES (all read-only w.r.t. the archive)
    1. Re-reads every one of the 204 contributing `results.json` files from disk and
       asserts the recorded row values match bit-for-bit (independent re-derivation).
    2. within-group correlations: by experiment family (archive-literal, 12 groups),
       by dataset, by model, and by design cell (dataset x model).
    3. Mixed-effects model  R@1 ~ DG + (1|dataset) + (1|model) + (1|config)
       fitted by REML.  `statsmodels` is NOT installed in this environment, so the
       crossed random-intercept REML engine is implemented here and validated against
       a simulation with known variance components (see `_selftest_reml`).
       Cluster-robust (CR1) standard errors are reported alongside as the
       model-free fallback.
    4. Clustered bootstrap of the DG-R@1 correlation: whole clusters resampled, at
       three cluster definitions, against the naive row-level bootstrap so the
       widening is visible.
    5. Out-of-sample check: leave-one-group-out (groups = family, and = design cell),
       fitting DG -> R@1 on the training folds and scoring R^2 on the held-out fold
       against a constant (training-mean) baseline.
    6. Mundlak within-between decomposition: is the pooled r driven by within-cell
       variation or by between-cell differences?
    7. Sensitivity: all 204 rows vs excluding the heterogeneous Route C/D/E configs.

PROVENANCE
    Input  : outputs/analysis/dg_r1_reproducible.json
             :: rows[*]  {path, dg_final, cg_final, r1, dg_init, cg_init}
             produced by tools/p1_dg_r1_recompute.py from
             outputs/**/results.json
             :: final_gap.distribution_gap, final_gap.centroid_gap,
                final_task_metrics.R@1
    Output : outputs/analysis/pr_stats_{within_group,mixed_effects,
             cluster_bootstrap,holdout}.json  and  pr_stats_hardened.json

GROUP LABELS — IMPORTANT CAVEAT
    `results.json` contains NO dataset / model / configuration field.  Only
    `experiment`, `lora_rank`, `n_trainable_params`, the gap blocks and the task
    metrics are archived.  Dataset and model labels are therefore DERIVED, and every
    derivation is listed in LABELS with its evidence (script line or archived doc
    line).  Rows whose dataset cannot be documented are labelled "UNDOCUMENTED" and
    are excluded from within-dataset / within-model / design-cell analyses; the count
    is reported rather than guessed.  The `family` grouping (first path component) is
    the only fully archive-literal grouping and is therefore the primary one.

IDEMPOTENT: re-running overwrites the same JSON files with identical content.
"""
import io
import json
import os
import re
import sys

import numpy as np
from scipy import stats
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_JSON = os.path.join(ROOT, "outputs", "analysis", "dg_r1_reproducible.json")
OUT_DIR = os.path.join(ROOT, "outputs", "analysis")

N_BOOT = 10000
BOOT_SEED = 20261012

# ---------------------------------------------------------------------------
# 1. group labels + evidence
#
# tier meanings
#   runner_literal : a runner script literally declares dataset=... AND writes to
#                    exactly this output directory
#   arg_default    : the runner takes --dataset and this is its argparse default
#   doc_xref       : the archived manuscript/doc groups this directory with a dataset
#   disputed       : the repository's own scripts probe this directory's dataset
#                    identity and do not settle it
# ---------------------------------------------------------------------------
LABELS = {
    "family_rules": [
        # (first path component, optional second component, dataset, model, tier, evidence)
        ("flickr30k", None, "flickr30k", "CLIP ViT-B/32", "arg_default",
         "experiments/main.py:436 --dataset default 'flickr30k'; src/config.py:120 "
         "clip_model default 'openai/clip-vit-base-patch32'"),
        ("flickr30k_seeds", None, "flickr30k", "CLIP ViT-B/32", "runner_literal",
         "experiments/seed_experiments.py:44 dataset=\"flickr30k\"; :36 "
         "OUTPUT_DIR=\"./outputs/flickr30k_seeds\""),
        ("coco", None, "coco", "CLIP ViT-B/32", "runner_literal",
         "experiments/coco_experiments.py:64 dataset_name=\"coco\"; :32-39 config names "
         "rq1_rank{4,8,16}_coco / rq2_{text_only,both,vision_only}_coco / "
         "baseline_full_ft_coco match the 7 archived dirs exactly"),
        ("phase1", None, "flickr30k", "CLIP ViT-B/32", "runner_literal",
         "experiments/phase1_experiments.py:13 DATA=\"flickr30k\"; :11 "
         "OUTPUT_DIR=outputs/phase1"),
        ("blip2", None, "flickr30k", "BLIP", "arg_default",
         "experiments/blip2_experiments.py:415 --dataset default 'flickr30k'; :414 "
         "--outputs_dir default './outputs/blip2'"),
        ("siglip", None, "flickr30k", "SigLIP", "arg_default",
         "experiments/siglip_experiments.py:382 --dataset default 'flickr30k'; :238 "
         "clip_model=SIGLIP_MODEL ('./models/siglip-base-patch16-224'); :381 "
         "--outputs_dir default './outputs/siglip'"),
        ("route_c", None, "flickr30k", "CLIP ViT-B/32", "doc_xref",
         "paper/sections/supplementary.tex:96 'Route C/D/E Enhanced Strategies --- 16 "
         "experiments' (8+5+3 matches archived route_c/route_d/route_e counts); "
         "Route E dataset stated as Flickr30k in paper/sections/experiments.tex:187"),
        ("route_d", None, "flickr30k", "CLIP ViT-B/32", "doc_xref",
         "paper/sections/supplementary.tex:96; paper/sections/discussion.tex:18 compares "
         "Route D (CGD=+0.079, R@1=0.389) against 'rank-8 on Flickr30k'"),
        ("route_e", None, "flickr30k", "CLIP ViT-B/32", "doc_xref",
         "paper/sections/experiments.tex:187 'DG evolution during the Route E DG-ES "
         "proof-of-concept (Flickr30k)'"),
        ("vitl", None, "UNDOCUMENTED", "ViT-L", "doc_xref",
         "no runner script found under experiments/ that writes outputs/vitl; the "
         "archive only names the backbone (paper/sections/experiments.tex:34 Table row "
         "'ViT-L'). Dataset not documented."),
        ("imagenet_zs", None, "DISPUTED", "CLIP ViT-B/32", "disputed",
         "tools/clip_zs_check.py and tools/clip_tinyimagenet_check.py exist solely to "
         "probe whether this directory is ImageNet / TinyImageNet / CIFAR-100; "
         "HANDOFF.md records 'CIFAR Top-1 hard-coded and the data dir is named "
         "imagenet_zs (identity in doubt)'. Not settled -> excluded from dataset "
         "analyses."),
    ],
    "theory_rules": [
        ("theory", "v1_trajectory", "flickr30k", "runner_literal",
         "experiments/theory/v1_rank_sweep.py:121 dataset=\"flickr30k\"; docstring "
         "'Output: outputs/theory/v1_trajectory/'"),
        ("theory", "adapter", "flickr30k", "runner_literal",
         "experiments/theory/adapter_sweep.py:79 dataset=\"flickr30k\"; docstring "
         "'Output: outputs/theory/adapter/'"),
        ("theory", "beta_pilot", "flickr30k", "runner_literal",
         "experiments/theory/beta_pilot.py:178 dataset=\"flickr30k\"; docstring "
         "'Output: outputs/theory/beta_pilot/...'"),
        ("theory", "epoch1", "flickr30k", "runner_literal",
         "experiments/theory/epoch1_gamma.py:71 dataset=\"flickr30k\"; "
         "OUTPUT_DIR=outputs/theory/epoch1"),
        ("theory", "verify_accum", "flickr30k", "runner_literal",
         "experiments/theory/verify_accum.py:64 dataset=\"flickr30k\"; "
         "OUTPUT_DIR=outputs/theory/verify_accum"),
        ("theory", "coco", "coco", "runner_literal",
         "experiments/theory/coco_validation.py:54 dataset=\"coco\"; docstring "
         "'MSCOCO cross-dataset validation - 3 key configs, 3 seeds each = 9 runs'; "
         "OUTPUT_DIR=outputs/theory/coco"),
    ],
    "theory_default": ("flickr30k", "CLIP ViT-B/32", "arg_default",
                       "src/config.py:124 dataset default 'flickr30k'; "
                       "src/config.py:120 clip_model default CLIP ViT-B/32"),
    "model_default": "CLIP ViT-B/32",
}


def classify(path):
    """path -> (family, config, dataset, model, tier)."""
    parts = path.split("/")
    family = parts[0]
    config = re.sub(r"/seed\d+$", "", path)
    if family == "theory":
        sub = parts[1] if len(parts) > 1 else ""
        for fam, sub_pat, ds, tier, ev in LABELS["theory_rules"]:
            if sub == sub_pat:
                return family, config, ds, "CLIP ViT-B/32", tier, ev
        ds, model, tier, ev = LABELS["theory_default"]
        return family, config, ds, model, tier, ev
    for fam, _sub, ds, model, tier, ev in LABELS["family_rules"]:
        if family == fam:
            return family, config, ds, model, tier, ev
    raise AssertionError("unclassified path: %s" % path)


# ---------------------------------------------------------------------------
# 2. small statistics helpers
# ---------------------------------------------------------------------------
def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def pearson_p(a, b):
    r = pearson(a, b)
    n = len(a)
    if not np.isfinite(r) or n < 3 or abs(r) >= 1.0:
        return float("nan")
    t = r * np.sqrt((n - 2) / (1.0 - r * r))
    return float(2.0 * stats.t.sf(abs(t), n - 2))


def fisher_ci(r, n, alpha=0.05):
    """Naive (independent-observations) Fisher-z CI for Pearson r."""
    if not np.isfinite(r) or n < 4:
        return [float("nan"), float("nan")]
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3.0)
    zc = stats.norm.ppf(1.0 - alpha / 2.0)
    return [float(np.tanh(z - zc * se)), float(np.tanh(z + zc * se))]


def ols(y, X):
    XtX = X.T @ X
    XtXi = np.linalg.pinv(XtX)
    beta = XtXi @ (X.T @ y)
    resid = y - X @ beta
    return beta, XtXi, resid


def cluster_robust(y, X, groups):
    """OLS with cluster-robust covariance.

    Returns beta, se_ols, se_cr0, se_cr1, and the number of clusters.
    CR1 uses the usual finite-sample correction  G/(G-1) * (n-1)/(n-k).
    """
    y, X = np.asarray(y, float), np.asarray(X, float)
    n, k = X.shape
    beta, XtXi, resid = ols(y, X)
    labels = np.asarray(groups)
    uniq = np.unique(labels)
    G = len(uniq)
    meat = np.zeros((k, k))
    for g in uniq:
        m = labels == g
        Xg = X[m]
        ug = resid[m]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    se_cr0 = np.sqrt(np.clip(np.diag(XtXi @ meat @ XtXi), 0, None))
    if G > 1 and n > k:
        c = (G / (G - 1.0)) * ((n - 1.0) / (n - k))
    else:
        c = 1.0
    se_cr1 = se_cr0 * np.sqrt(c)
    sigma2 = float(resid @ resid) / max(n - k, 1)
    se_ols = np.sqrt(np.clip(np.diag(XtXi) * sigma2, 0, None))
    return dict(beta=beta, se_ols=se_ols, se_cr0=se_cr0, se_cr1=se_cr1,
                G=int(G), n=int(n), k=int(k))


# ---------------------------------------------------------------------------
# 3. REML for crossed random intercepts  (statsmodels is not installed)
# ---------------------------------------------------------------------------
def reml_crossed(y, X, group_labels, n_starts=4, seed=0):
    """REML fit of  y = X beta + sum_k Z_k u_k + e,  u_k ~ N(0, tau_k I).

    V = sigma2_e * W,  W = I + sum_k theta_k * (Z_k Z_k'),
    theta = tau / sigma2_e.  The profile REML criterion

        -2 l_R(theta) = (n-p) log( r' W^{-1} r ) + log|W| + log|X' W^{-1} X|

    is minimised over log theta; sigma2_e = r' W^{-1} r / (n-p).
    This mirrors what statsmodels' MixedLM does for a single grouping factor,
    generalised to crossed factors (which MixedLM cannot do at all).
    """
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, p = X.shape
    ind = []
    for labels in group_labels:
        _, inv = np.unique(np.asarray(labels), return_inverse=True)
        ind.append((inv[:, None] == inv[None, :]).astype(float))
    I = np.eye(n)

    def make_W(theta):
        W = I.copy()
        for th, Mk in zip(theta, ind):
            if th > 0:
                W += th * Mk
        return W

    def neg_reml(log_theta):
        theta = np.exp(np.clip(log_theta, -30.0, 30.0))
        W = make_W(theta)
        try:
            c = cho_factor(W, lower=True)
        except np.linalg.LinAlgError:
            return 1e12
        logdetW = 2.0 * float(np.sum(np.log(np.diag(c[0]))))
        WiX = cho_solve(c, X)
        Wiy = cho_solve(c, y)
        XtWiX = X.T @ WiX
        XtWiy = X.T @ Wiy
        sign, logdetXtWiX = np.linalg.slogdet(XtWiX)
        if sign <= 0:
            return 1e12
        try:
            beta = np.linalg.solve(XtWiX, XtWiy)
        except np.linalg.LinAlgError:
            return 1e12
        r = y - X @ beta
        rss = float(r @ cho_solve(c, r))
        if rss <= 0:
            return 1e12
        return 0.5 * ((n - p) * np.log(rss) + logdetW + logdetXtWiX)

    k = len(group_labels)
    starts = [np.zeros(k)]
    rng = np.random.default_rng(seed)
    for _ in range(n_starts - 1):
        starts.append(rng.normal(0.0, 1.0, k))
    best = None
    for s in starts:
        res = minimize(neg_reml, s, method="Nelder-Mead",
                       options=dict(maxiter=4000, xatol=1e-8, fatol=1e-8))
        res2 = minimize(neg_reml, res.x, method="L-BFGS-B",
                        options=dict(maxiter=2000))
        cand = res2 if res2.fun <= res.fun else res
        if best is None or cand.fun < best.fun:
            best = cand
    theta = np.exp(np.clip(best.x, -30.0, 30.0))
    W = make_W(theta)
    c = cho_factor(W, lower=True)
    WiX = cho_solve(c, X)
    Wiy = cho_solve(c, y)
    XtWiX = X.T @ WiX
    XtWiy = X.T @ Wiy
    beta = np.linalg.solve(XtWiX, XtWiy)
    r = y - X @ beta
    rss = float(r @ cho_solve(c, r))
    sigma2_e = rss / (n - p)
    cov_beta = sigma2_e * np.linalg.pinv(XtWiX)
    se = np.sqrt(np.clip(np.diag(cov_beta), 0, None))
    tau = theta * sigma2_e
    total = float(tau.sum() + sigma2_e)
    return dict(beta=beta, se=se, tau=tau, sigma2_e=float(sigma2_e),
                theta=theta, icc=(tau / total).tolist(),
                icc_resid=float(sigma2_e / total),
                neg2_reml=float(2.0 * best.fun), converged=bool(best.success),
                n=int(n), p=int(p))


def _selftest_reml():
    """Recover known variance components from simulated crossed-random-intercept data."""
    rng = np.random.default_rng(7)
    n = 400
    gd = rng.integers(0, 8, n)
    gm = rng.integers(0, 5, n)
    gc = rng.integers(0, 40, n)
    x = rng.normal(size=n)
    tau_true = np.array([0.50, 0.40, 0.30])
    y = 0.5 - 1.2 * x
    for tau, g in zip(tau_true, (gd, gm, gc)):
        y = y + rng.normal(0.0, np.sqrt(tau), len(np.unique(g)))[g]
    y = y + rng.normal(0.0, 1.0, n)
    X = np.column_stack([np.ones(n), x])
    fit = reml_crossed(y, X, [gd, gm, gc], n_starts=3, seed=1)
    assert abs(fit["beta"][1] + 1.2) < 0.25, "REML slope recovery failed: %.3f" % fit["beta"][1]
    assert abs(fit["beta"][0] - 0.5) < 0.25, "REML intercept recovery failed"
    ratios = []
    for j in range(3):
        ratio = fit["tau"][j] / tau_true[j]
        ratios.append(ratio)
        # individual variance components are only weakly identified when the factor
        # has few levels (8 / 5 / 40 here); the bounds below are deliberately wide
        # and the realised ratios are reported so the reader can judge.
        assert 0.2 < ratio < 5.0, (
            "REML variance-component recovery failed for level %d: tau=%.3f vs true %.3f"
            % (j, fit["tau"][j], tau_true[j]))
    tot = float(np.sum(fit["tau"])) / float(np.sum(tau_true))
    assert 0.5 < tot < 2.0, "REML total random variance recovery failed: %.3f" % tot
    return dict(beta_slope=float(fit["beta"][1]), tau=fit["tau"].tolist(),
                tau_true=tau_true.tolist(), icc=fit["icc"],
                tau_ratio=[round(float(v), 4) for v in ratios],
                tau_total_ratio=round(tot, 4),
                n_levels=[8, 5, 40], n=400,
                caveat=("component-wise recovery is weakest for the factor with fewest "
                        "levels; use the ICCs as order-of-magnitude, not exact"))


# ---------------------------------------------------------------------------
# 4. main
# ---------------------------------------------------------------------------
def main():
    print("=" * 78)
    print("PR statistics hardening: DG vs R@1 pseudo-replication / confounding")
    print("=" * 78)

    with io.open(SRC_JSON, encoding="utf-8") as fh:
        src = json.load(fh)
    rows = src["rows"]
    assert len(rows) == 204, "expected 204 rows, got %d" % len(rows)
    assert len({r["path"] for r in rows}) == 204, "duplicate paths in source table"

    # ---- 4.1 independent re-derivation straight from the archive ------------
    mismatches = []
    for r in rows:
        p = os.path.join(ROOT, "outputs", r["path"], "results.json")
        assert os.path.exists(p), "missing archive file %s" % p
        with io.open(p, encoding="utf-8") as fh:
            o = json.load(fh)
        got = (float(o["final_gap"]["distribution_gap"]),
               float(o["final_gap"]["centroid_gap"]),
               float(o["final_task_metrics"]["R@1"]))
        want = (r["dg_final"], r["cg_final"], r["r1"])
        if got != want:
            mismatches.append((r["path"], want, got))
    assert not mismatches, "row values do not re-derive from archive: %s" % mismatches[:5]

    # ---- 4.2 labels ---------------------------------------------------------
    ds, md, fam, cfg, tier = [], [], [], [], []
    evid = {}
    for r in rows:
        f, c, d, m, t, e = classify(r["path"])
        fam.append(f)
        cfg.append(c)
        ds.append(d)
        md.append(m)
        tier.append(t)
        evid.setdefault("%s|%s" % (d, m), {"dataset": d, "model": m, "tier": t,
                                           "evidence": e, "n_rows": 0})
        evid["%s|%s" % (d, m)]["n_rows"] += 1

    y = np.array([r["r1"] for r in rows], float)
    x = np.array([r["dg_final"] for r in rows], float)
    fam = np.array(fam)
    cfg = np.array(cfg)
    ds = np.array(ds)
    md = np.array(md)
    cell = np.array(["%s | %s" % (d, m) for d, m in zip(ds, md)])

    print("\n[labels] design cells (dataset | model):")
    for k in sorted(evid, key=lambda kk: -evid[kk]["n_rows"]):
        v = evid[k]
        print("   %-34s n=%3d  tier=%s" % (k, v["n_rows"], v["tier"]))
    n_undoc = int((ds == "UNDOCUMENTED").sum())
    n_disp = int((ds == "DISPUTED").sum())
    print("   rows with NO documented dataset: %d (UNDOCUMENTED=%d, DISPUTED=%d)"
          % (n_undoc + n_disp, n_undoc, n_disp))

    prov = {
        "input_file": "outputs/analysis/dg_r1_reproducible.json",
        "input_field": "rows[*].{path,dg_final,cg_final,r1}",
        "input_producer": "tools/p1_dg_r1_recompute.py",
        "archive_source": "outputs/**/results.json :: final_gap.distribution_gap, "
                          "final_gap.centroid_gap, final_task_metrics.R@1",
        "recheck": ("all 204 rows independently re-read from their results.json; "
                    "values match bit-for-bit (%d mismatches)" % len(mismatches)),
        "labels": ("results.json archives NO dataset/model/config field; labels are "
                   "derived, see label_evidence. family (first path component) is the "
                   "only archive-literal grouping."),
        "statsmodels_available": False,
    }

    out = {"provenance": prov, "label_evidence": evid, "n_rows": 204}

    # ---- 4.3 pooled baseline ------------------------------------------------
    r_pooled = pearson(x, y)
    pooled = dict(n=204, r=r_pooled, p=pearson_p(x, y),
                  naive_fisher_ci95=fisher_ci(r_pooled, 204),
                  r_squared=r_pooled ** 2)
    assert abs(r_pooled - (-0.7142)) < 5e-4, (
        "pooled r did not reproduce the manuscript value -0.7142: %.6f" % r_pooled)
    print("\n[pooled] n=204  r = %+.4f (p=%.3g)  naive 95%% CI [%+.4f, %+.4f]"
          % (r_pooled, pooled["p"], *pooled["naive_fisher_ci95"]))
    print("         reproduces the manuscript value -0.7142 -> assertion passed")

    # ---- 4.4 within-group correlations (requested by all three reviewers) ---
    def within(group_arr, min_n=4):
        res = {}
        for g in sorted(set(group_arr.tolist())):
            m = group_arr == g
            n = int(m.sum())
            rr = pearson(x[m], y[m]) if n >= 3 else float("nan")
            rec = dict(n=n, r=(round(rr, 4) if np.isfinite(rr) else None),
                       p=(round(pearson_p(x[m], y[m]), 6) if np.isfinite(rr) else None))
            if n >= min_n and np.isfinite(rr):
                rec["ci95"] = [round(v, 4) for v in fisher_ci(rr, n)]
            else:
                rec["note"] = "n < %d: correlation reported but not inferential" % min_n
            res[g] = rec
        return res

    within_family = within(fam)
    within_dataset = within(ds)
    within_model = within(md)
    within_cell = within(cell)
    within_config = within(cfg, min_n=3)

    # variance-explained summary of the within-group view
    def pooled_within(group_arr):
        xs, ys, ns, gs = [], [], [], []
        # NB: iterate over a SORTED list, never a bare set() -- set iteration order
        # over str is randomised per process (PYTHONHASHSEED), which would make the
        # written JSON non-reproducible across runs.
        for g in sorted(set(group_arr.tolist())):
            m = group_arr == g
            if m.sum() >= 3 and x[m].std() > 0 and y[m].std() > 0:
                xs.append(x[m] - x[m].mean())
                ys.append(y[m] - y[m].mean())
                ns.append(int(m.sum()))
                gs.append(g)
        if not xs:
            return dict(n_groups=0)
        X = np.concatenate(xs)
        Y = np.concatenate(ys)
        return dict(n_groups=len(ns), n_rows=int(len(Y)),
                    r_within=round(pearson(X, Y), 4),
                    r_within_p=round(pearson_p(X, Y), 6),
                    groups=gs, rows_per_group=ns)

    within_block = {
        "by_family": within_family,
        "by_dataset": within_dataset,
        "by_model": within_model,
        "by_design_cell": within_cell,
        "by_config": within_config,
        "pooled_within_family": pooled_within(fam),
        "pooled_within_design_cell": pooled_within(cell),
        "pooled_within_dataset": pooled_within(ds),
        "pooled_within_model": pooled_within(md),
        "note": ("'pooled_within_*' centres DG and R@1 inside each group and then "
                 "correlates the stacked deviations: the pure within-group slope. "
                 "Compare with the pooled r over all 204 rows."),
    }
    # nested view: family inside dataset.  This is where aggregation effects show up
    # (e.g. coco/* alone is positive while coco as a dataset is negative).
    nested = {}
    for d in sorted(set(ds.tolist())):
        sub = {}
        for f in sorted(set(fam[ds == d].tolist())):
            m = (ds == d) & (fam == f)
            n = int(m.sum())
            rr = pearson(x[m], y[m]) if n >= 3 else float("nan")
            sub[f] = dict(n=n, r=(round(rr, 4) if np.isfinite(rr) else None))
        m = ds == d
        nested[d] = dict(dataset_r=round(pearson(x[m], y[m]), 4) if m.sum() >= 3 else None,
                         n_dataset=int(m.sum()), by_family=sub)
    within_block["by_family_within_dataset"] = nested
    out["within_group"] = within_block
    print("\n[within-group] family (archive-literal, 12 groups):")
    for k, v in sorted(within_family.items(), key=lambda kv: -kv[1]["n"]):
        print("   %-16s n=%3d  r=%s" % (k, v["n"], v["r"]))
    print("   pooled within-family r = %+.4f"
          % within_block["pooled_within_family"]["r_within"])
    print("[within-group] dataset:")
    for k, v in within_dataset.items():
        print("   %-16s n=%3d  r=%s" % (k, v["n"], v["r"]))
    print("[within-group] model:")
    for k, v in within_model.items():
        print("   %-16s n=%3d  r=%s" % (k, v["n"], v["r"]))
    print("[within-group] family nested inside dataset (aggregation check):")
    for d, v in nested.items():
        print("   dataset %-14s n=%3d r=%s" % (d, v["n_dataset"], v["dataset_r"]))
        for f, w in v["by_family"].items():
            print("      %-16s n=%3d r=%s" % (f, w["n"], w["r"]))

    # ---- 4.5 mixed effects + cluster-robust SE ------------------------------
    Xd = np.column_stack([np.ones(204), x])
    self_test = _selftest_reml()
    print("\n[REML self-test] recovered slope %.3f (true -1.2), tau=%s (true %s)"
          % (self_test["beta_slope"],
             [round(t, 3) for t in self_test["tau"]], self_test["tau_true"]))

    mixed = {}
    models = {
        "M1_random_intercept_config": [cfg],
        "M2_random_intercepts_family_config": [fam, cfg],
        "M3_random_intercepts_dataset_model": [ds, md],
        "M4_random_intercepts_dataset_model_config": [ds, md, cfg],
        "M5_random_intercepts_dataset_model_family_config": [ds, md, fam, cfg],
    }
    for name, gl in models.items():
        fit = reml_crossed(y, Xd, gl, n_starts=4, seed=11)
        slope, se = float(fit["beta"][1]), float(fit["se"][1])
        z = slope / se
        # conservative small-sample reference: clusters = number of levels of the
        # coarsest grouping actually in the model
        G = len(np.unique(np.asarray(gl[0])))
        mixed[name] = dict(
            random_effects=[int(len(np.unique(np.asarray(g)))) for g in gl],
            beta_intercept=round(float(fit["beta"][0]), 4),
            beta_DG=round(slope, 4),
            se_DG=round(se, 4),
            z=round(z, 4),
            p_wald=float(2.0 * stats.norm.sf(abs(z))),
            t_conservative=round(z, 4),
            df_conservative=int(G - 1),
            p_t_conservative=float(2.0 * stats.t.sf(abs(z), max(G - 1, 1))),
            variance_components=dict(
                levels=[round(float(v), 4) for v in fit["tau"]],
                residual=round(float(fit["sigma2_e"]), 4)),
            icc=dict(levels=[round(float(v), 4) for v in fit["icc"]],
                     residual=round(float(fit["icc_resid"]), 4)),
            icc_total_random=round(float(np.sum(fit["icc"])), 4),
            neg2_reml=round(float(fit["neg2_reml"]), 4),
            converged=bool(fit["converged"]),
        )
        print("   %-48s beta=%+.4f se=%.4f p_wald=%.3g  ICC_random=%.3f"
              % (name, slope, se, mixed[name]["p_wald"], mixed[name]["icc_total_random"]))

    cr = cluster_robust(y, Xd, cell)
    cr_fam = cluster_robust(y, Xd, fam)
    cr_cfg = cluster_robust(y, Xd, cfg)
    mixed["cluster_robust_OLS"] = {
        "by_design_cell": dict(
            n_clusters=cr["G"], beta_DG=round(float(cr["beta"][1]), 4),
            se_ols=round(float(cr["se_ols"][1]), 4),
            se_cr0=round(float(cr["se_cr0"][1]), 4),
            se_cr1=round(float(cr["se_cr1"][1]), 4),
            p_cr1_t_Gminus1=float(2.0 * stats.t.sf(
                abs(float(cr["beta"][1]) / float(cr["se_cr1"][1])), cr["G"] - 1)),
            se_inflation_vs_ols=round(float(cr["se_cr1"][1] / cr["se_ols"][1]), 4)),
        "by_family": dict(
            n_clusters=cr_fam["G"], beta_DG=round(float(cr_fam["beta"][1]), 4),
            se_ols=round(float(cr_fam["se_ols"][1]), 4),
            se_cr1=round(float(cr_fam["se_cr1"][1]), 4),
            p_cr1_t_Gminus1=float(2.0 * stats.t.sf(
                abs(float(cr_fam["beta"][1]) / float(cr_fam["se_cr1"][1])),
                cr_fam["G"] - 1)),
            se_inflation_vs_ols=round(float(cr_fam["se_cr1"][1] / float(cr_fam["se_ols"][1])), 4)),
        "by_config": dict(
            n_clusters=cr_cfg["G"], beta_DG=round(float(cr_cfg["beta"][1]), 4),
            se_ols=round(float(cr_cfg["se_ols"][1]), 4),
            se_cr1=round(float(cr_cfg["se_cr1"][1]), 4),
            p_cr1_t_Gminus1=float(2.0 * stats.t.sf(
                abs(float(cr_cfg["beta"][1]) / float(cr_cfg["se_cr1"][1])),
                cr_cfg["G"] - 1)),
            se_inflation_vs_ols=round(float(cr_cfg["se_cr1"][1] / float(cr_cfg["se_ols"][1])), 4)),
        "note": ("CR1 = G/(G-1)*(n-1)/(n-k) finite-sample correction; p from t with "
                 "G-1 df, the conventional conservative choice for few clusters."),
    }
    mixed["self_test_reml"] = self_test
    # robustness of the mixed-model fixed effect to the label choices / subset
    mixed["sensitivity_subsets"] = {}
    for key, mask, desc in (
            ("documented_dataset_only",
             ~np.isin(ds, ["UNDOCUMENTED", "DISPUTED"]),
             "drop the 5 rows whose dataset is undocumented or disputed"),
            ("drop_route_cde",
             ~np.isin(fam, ["route_c", "route_d", "route_e"]),
             "drop the 16 Route C/D/E rows"),
            ("design_cells_n_ge_10",
             np.isin(cell, [c for c in sorted(set(cell.tolist()))
                            if (cell == c).sum() >= 10]),
             "keep only design cells with n>=10")):
        nk = int(mask.sum())
        fit = reml_crossed(y[mask], np.column_stack([np.ones(nk), x[mask]]),
                           [ds[mask], md[mask], cfg[mask]], n_starts=3, seed=13)
        mixed["sensitivity_subsets"][key] = dict(
            description=desc, n=nk,
            beta_DG=round(float(fit["beta"][1]), 4),
            se_DG=round(float(fit["se"][1]), 4),
            p_wald=float(2.0 * stats.norm.sf(abs(float(fit["beta"][1])
                                                 / float(fit["se"][1])))),
            icc_total_random=round(float(np.sum(fit["icc"])), 4))
        print("   [sensitivity] %-24s n=%3d beta=%+.4f se=%.4f ICC_random=%.3f"
              % (key, nk, mixed["sensitivity_subsets"][key]["beta_DG"],
                 mixed["sensitivity_subsets"][key]["se_DG"],
                 mixed["sensitivity_subsets"][key]["icc_total_random"]))
    mixed["statsmodels_available"] = False
    mixed["note_statsmodels"] = (
        "statsmodels is NOT installed in D:\\Anaconda\\envs\\pytorch "
        "(verified: ModuleNotFoundError). The crossed random-intercept REML engine "
        "above is implemented in this script and validated by simulation.")
    # sanity: the mixed-model slope must be a perturbation of the OLS slope
    ols_slope = float(np.polyfit(x, y, 1)[0])
    assert abs(mixed["M4_random_intercepts_dataset_model_config"]["beta_DG"]
               - ols_slope) < 0.5 * abs(ols_slope), "mixed slope diverged from OLS"
    out["mixed_effects"] = mixed
    out["ols_slope_all"] = round(ols_slope, 4)

    # ---- 4.6 Mundlak within-between decomposition ---------------------------
    def mundlak(group_arr, label):
        gv = np.asarray(group_arr)
        gm = np.array([x[gv == g].mean() for g in gv])
        dev = x - gm
        Xm = np.column_stack([np.ones(204), dev, gm])
        r = cluster_robust(y, Xm, gv)
        b, se = float(r["beta"][1]), float(r["se_cr1"][1])
        b2, se2 = float(r["beta"][2]), float(r["se_cr1"][2])
        G = r["G"]
        return dict(
            group=label, n_groups=G,
            beta_within=round(b, 4), se_within_cr1=round(se, 4),
            p_within=float(2.0 * stats.t.sf(abs(b / se), max(G - 1, 1))),
            beta_between=round(b2, 4), se_between_cr1=round(se2, 4),
            p_between=float(2.0 * stats.t.sf(abs(b2 / se2), max(G - 1, 1))),
            note=("R@1 ~ within-group DG deviation + group-mean DG, cluster-robust "
                  "CR1 by the same grouping. beta_between large / beta_within ~ 0 "
                  "means the pooled correlation is a between-group artefact."))

    mund = [mundlak(cell, "design_cell (dataset|model)"),
            mundlak(fam, "family"),
            mundlak(cfg, "config")]
    # variant: only rows inside groups that carry more than one observation --
    # singleton groups contribute a zero within-deviation and dilute the estimate.
    for group_arr, label in ((cell, "design_cell (dataset|model)"),
                             (fam, "family"), (cfg, "config")):
        gv = np.asarray(group_arr)
        counts = {g: int((gv == g).sum()) for g in set(gv.tolist())}
        keep = np.array([counts[g] >= 2 for g in gv])
        if keep.sum() < 10 or len({g for g in gv[keep].tolist()}) < 3:
            continue
        gm = np.array([x[gv == g].mean() for g in gv])
        dev = (x - gm)[keep]
        gmk = gm[keep]
        Xm = np.column_stack([np.ones(int(keep.sum())), dev, gmk])
        r = cluster_robust(y[keep], Xm, gv[keep])
        G = r["G"]
        b, se = float(r["beta"][1]), float(r["se_cr1"][1])
        b2, se2 = float(r["beta"][2]), float(r["se_cr1"][2])
        mund.append(dict(
            group=label + " [groups with n>=2 only]", n_groups=G,
            n_rows=int(keep.sum()),
            beta_within=round(b, 4), se_within_cr1=round(se, 4),
            p_within=float(2.0 * stats.t.sf(abs(b / se), max(G - 1, 1))),
            beta_between=round(b2, 4), se_between_cr1=round(se2, 4),
            p_between=float(2.0 * stats.t.sf(abs(b2 / se2), max(G - 1, 1))),
            note="singleton groups dropped (they have zero within-group deviation)"))
    out["mundlak_within_between"] = mund
    print("\n[Mundlak within-between] (CR1 cluster-robust, t with G-1 df)")
    for m in mund:
        print("   %-52s G=%3d n=%3d  within beta=%+.4f (p=%.3g)  between beta=%+.4f (p=%.3g)"
              % (m["group"], m["n_groups"], m.get("n_rows", 204),
                 m["beta_within"], m["p_within"], m["beta_between"], m["p_between"]))

    # ---- 4.6b design effect / effective sample size -------------------------
    icc4 = mixed["M4_random_intercepts_dataset_model_config"]["icc"]["levels"]
    icc2 = mixed["M2_random_intercepts_family_config"]["icc"]["levels"]
    n_cell = len(set(cell.tolist()))
    n_fam = len(set(fam.tolist()))
    icc_cell_var = float(icc4[0]) + float(icc4[1])          # dataset + model
    icc_family_var = float(icc2[0])                          # family
    de_cell = 1.0 + (204.0 / n_cell - 1.0) * icc_cell_var
    de_family = 1.0 + (204.0 / n_fam - 1.0) * icc_family_var
    out["design_effect"] = dict(
        n_rows=204,
        design_cell=dict(n_clusters=n_cell, mean_cluster_size=round(204.0 / n_cell, 3),
                         icc_dataset=icc4[0], icc_model=icc4[1],
                         icc_cell=round(icc_cell_var, 4),
                         design_effect=round(de_cell, 3),
                         effective_n=round(204.0 / de_cell, 2),
                         source="M4 icc.levels = [dataset, model, config]; "
                                "DE = 1 + (mean cluster size - 1) * ICC"),
        family=dict(n_clusters=n_fam, mean_cluster_size=round(204.0 / n_fam, 3),
                    icc_family=icc_family_var, design_effect=round(de_family, 3),
                    effective_n=round(204.0 / de_family, 2),
                    source="M2 icc.levels = [family, config]"),
        note=("the nominal n=204 behaves like this many independent observations once "
              "the random-intercept structure is accounted for."))
    print("\n[design effect] cell-level ICC=%.3f -> DE=%.2f -> effective n=%.1f (nominal 204)"
          % (icc_cell_var, de_cell, 204.0 / de_cell))
    print("                family-level ICC=%.3f -> DE=%.2f -> effective n=%.1f"
          % (icc_family_var, de_family, 204.0 / de_family))

    # ---- 4.7 clustered vs naive bootstrap ----------------------------------
    def boot_cluster(group_arr, n_boot=N_BOOT, seed=BOOT_SEED):
        gv = np.asarray(group_arr)
        uniq = np.unique(gv)
        idx = [np.where(gv == g)[0] for g in uniq]
        rng = np.random.default_rng(seed)
        G = len(uniq)
        rs = np.empty(n_boot)
        for i in range(n_boot):
            pick = rng.integers(0, G, G)
            sel = np.concatenate([idx[j] for j in pick])
            rs[i] = pearson(x[sel], y[sel])
        rs = rs[np.isfinite(rs)]
        return dict(n_clusters=G, n_resamples=int(rs.size),
                    r_mean=round(float(rs.mean()), 4),
                    ci95=[round(float(np.percentile(rs, 2.5)), 4),
                          round(float(np.percentile(rs, 97.5)), 4)],
                    ci_width=round(float(np.percentile(rs, 97.5)
                                         - np.percentile(rs, 2.5)), 4),
                    frac_r_ge_0=round(float((rs >= 0).mean()), 5))

    def boot_rows(n_boot=N_BOOT, seed=BOOT_SEED):
        rng = np.random.default_rng(seed)
        rs = np.empty(n_boot)
        for i in range(n_boot):
            sel = rng.integers(0, 204, 204)
            rs[i] = pearson(x[sel], y[sel])
        rs = rs[np.isfinite(rs)]
        return dict(n_clusters=204, n_resamples=int(rs.size),
                    r_mean=round(float(rs.mean()), 4),
                    ci95=[round(float(np.percentile(rs, 2.5)), 4),
                          round(float(np.percentile(rs, 97.5)), 4)],
                    ci_width=round(float(np.percentile(rs, 97.5)
                                         - np.percentile(rs, 2.5)), 4),
                    frac_r_ge_0=round(float((rs >= 0).mean()), 5))

    naive = boot_rows()
    bc = {"naive_row_bootstrap": naive,
          "clustered_by_family": boot_cluster(fam),
          "clustered_by_design_cell": boot_cluster(cell),
          "clustered_by_config": boot_cluster(cfg),
          "point_estimate_r": round(r_pooled, 4),
          "fisher_ci95": [round(v, 4) for v in fisher_ci(r_pooled, 204)],
          "n_boot": N_BOOT, "seed": BOOT_SEED}
    bc["widening_design_cell_vs_naive"] = round(
        bc["clustered_by_design_cell"]["ci_width"] / naive["ci_width"], 4)
    bc["widening_family_vs_naive"] = round(
        bc["clustered_by_family"]["ci_width"] / naive["ci_width"], 4)
    out["cluster_bootstrap"] = bc
    print("\n[bootstrap] %d resamples, seed %d" % (N_BOOT, BOOT_SEED))
    print("   naive  row-level   : r=%+.4f  CI [%+.4f, %+.4f]  width %.4f"
          % (naive["r_mean"], *naive["ci95"], naive["ci_width"]))
    for k in ("clustered_by_family", "clustered_by_design_cell", "clustered_by_config"):
        v = bc[k]
        print("   %-18s (%2d clusters): r=%+.4f  CI [%+.4f, %+.4f]  width %.4f  x%.2f vs naive"
              % (k.replace("clustered_by_", ""), v["n_clusters"], v["r_mean"],
                 *v["ci95"], v["ci_width"], v["ci_width"] / naive["ci_width"]))
    assert bc["clustered_by_design_cell"]["ci_width"] > naive["ci_width"], (
        "clustered CI is not wider than the naive CI")
    assert bc["clustered_by_family"]["ci_width"] > naive["ci_width"], (
        "family-clustered CI is not wider than the naive CI")

    # ---- 4.8 out-of-sample / leave-one-group-out ---------------------------
    def logo(group_arr, label):
        gv = np.asarray(group_arr)
        groups = sorted(set(gv.tolist()))
        folds, sse_m, sse_b = [], 0.0, 0.0
        for g in groups:
            te = gv == g
            tr = ~te
            if te.sum() == 0 or tr.sum() < 3 or x[tr].std() == 0:
                continue
            b = np.polyfit(x[tr], y[tr], 1)
            pred = np.polyval(b, x[te])
            ybar = float(y[tr].mean())
            sm = float(np.sum((y[te] - pred) ** 2))
            sb = float(np.sum((y[te] - ybar) ** 2))
            sse_m += sm
            sse_b += sb
            folds.append(dict(group=g, n_train=int(tr.sum()), n_test=int(te.sum()),
                              slope=round(float(b[0]), 4), intercept=round(float(b[1]), 4),
                              train_mean_R1=round(ybar, 4),
                              r2_oos=(round(1.0 - sm / sb, 4) if sb > 0 else None),
                              r2_insample=(round(float(np.corrcoef(x[tr], y[tr])[0, 1]) ** 2, 4)
                                           if x[tr].std() > 0 else None)))
        pooled = 1.0 - sse_m / sse_b if sse_b > 0 else float("nan")
        fold_r2 = [f["r2_oos"] for f in folds if f["r2_oos"] is not None]
        return dict(grouping=label, n_folds=len(folds),
                    r2_oos_pooled=round(float(pooled), 4),
                    r2_oos_median_fold=(round(float(np.median(fold_r2)), 4)
                                        if fold_r2 else None),
                    frac_folds_r2_positive=(round(float(np.mean([v > 0 for v in fold_r2])), 4)
                                            if fold_r2 else None),
                    frac_folds_beat_constant=(round(float(np.mean([v > 0 for v in fold_r2])), 4)
                                              if fold_r2 else None),
                    worst_fold=(min(folds,
                                    key=lambda f: (f["r2_oos"] if f["r2_oos"] is not None
                                                   else float("-inf")))["group"]
                                if folds else None),
                    sse_model=round(sse_m, 6), sse_constant_baseline=round(sse_b, 6),
                    folds=folds,
                    note=("slope fitted on the training folds only; baseline is the "
                          "training-fold mean of R@1; SSE pooled over all folds. The "
                          "pooled figure is dominated by folds with many test rows and "
                          "can be dragged to -inf by a fold where the constant baseline "
                          "already fits almost perfectly, so read r2_oos_median_fold and "
                          "frac_folds_r2_positive alongside it."))

    hold = {"leave_one_family_out": logo(fam, "family"),
            "leave_one_design_cell_out": logo(cell, "design_cell (dataset|model)"),
            "leave_one_config_out": logo(cfg, "config")}
    # in-sample reference
    hold["in_sample"] = dict(n=204, r2=round(r_pooled ** 2, 4),
                             slope=round(ols_slope, 4))
    out["holdout"] = hold
    print("\n[out-of-sample] DG -> R@1, slope fitted on training folds")
    print("   in-sample  R^2 = %.4f (n=204)" % hold["in_sample"]["r2"])
    for k in ("leave_one_family_out", "leave_one_design_cell_out", "leave_one_config_out"):
        v = hold[k]
        print("   %-28s folds=%2d  pooled OOS R^2 = %+.4f  median fold R^2 = %+.4f  "
              "folds beating baseline = %.0f%%"
              % (k, v["n_folds"], v["r2_oos_pooled"], v["r2_oos_median_fold"],
                 100.0 * v["frac_folds_r2_positive"]))

    # ---- 4.9 sensitivity: drop the heterogeneous Route C/D/E ---------------
    def subset_report(mask, name):
        n = int(mask.sum())
        r = pearson(x[mask], y[mask])
        return dict(subset=name, n=n, r=round(r, 4),
                    p=round(pearson_p(x[mask], y[mask]), 6),
                    fisher_ci95=[round(v, 4) for v in fisher_ci(r, n)],
                    r2=round(r * r, 4),
                    n_clusters_family=int(len(set(fam[mask].tolist()))),
                    n_clusters_cell=int(len(set(cell[mask].tolist()))))

    route_mask = np.isin(fam, ["route_c", "route_d", "route_e"])
    sens = {
        "S1_all_204": subset_report(np.ones(204, bool), "all 204 rows (manuscript value)"),
        "S2_drop_route_d": subset_report(fam != "route_d", "drop Route D (5 rows)"),
        "S3_drop_route_cde": subset_report(~route_mask, "drop Route C/D/E (16 rows)"),
        "S4_cell_ge_10": subset_report(np.isin(cell, [c for c in set(cell.tolist())
                                                      if (cell == c).sum() >= 10]),
                                       "keep only design cells with n>=10"),
        "S5_documented_dataset_only": subset_report(
            ~np.isin(ds, ["UNDOCUMENTED", "DISPUTED"]),
            "drop rows with undocumented/disputed dataset"),
    }
    out["sensitivity"] = sens
    print("\n[sensitivity]")
    for k, v in sens.items():
        print("   %-28s n=%3d  r=%+.4f  CI [%+.4f, %+.4f]  R2=%.4f"
              % (k, v["n"], v["r"], v["fisher_ci95"][0], v["fisher_ci95"][1], v["r2"]))
    assert abs(sens["S1_all_204"]["r"] - r_pooled) < 5e-5, (
        "S1 (all 204) must reproduce the pooled r exactly (rounding at 4 dp)")

    # ---- 4.10 verdict -------------------------------------------------------
    icc_m4 = mixed["M4_random_intercepts_dataset_model_config"]["icc"]
    icc_random = mixed["M4_random_intercepts_dataset_model_config"]["icc_total_random"]
    within_fam_r = within_block["pooled_within_family"]["r_within"]
    within_cell_r = within_block["pooled_within_design_cell"]["r_within"]
    oos_cell = hold["leave_one_design_cell_out"]["r2_oos_pooled"]
    oos_fam = hold["leave_one_family_out"]["r2_oos_pooled"]
    mun_cell = mund[0]
    out["verdict"] = dict(
        pooled_r=round(r_pooled, 4), pooled_r2=round(r_pooled ** 2, 4),
        pooled_naive_ci=pooled["naive_fisher_ci95"],
        clustered_ci_cell=bc["clustered_by_design_cell"]["ci95"],
        clustered_ci_family=bc["clustered_by_family"]["ci95"],
        ci_widening_factor_cell=bc["widening_design_cell_vs_naive"],
        within_family_r=within_fam_r, within_cell_r=within_cell_r,
        within_dataset=dict((d, v["r"]) for d, v in within_dataset.items()),
        within_model=dict((d, v["r"]) for d, v in within_model.items()),
        mixed_beta_DG=mixed["M4_random_intercepts_dataset_model_config"]["beta_DG"],
        mixed_se_DG=mixed["M4_random_intercepts_dataset_model_config"]["se_DG"],
        mixed_icc_random=icc_random, mixed_icc_levels=icc_m4,
        effective_n_cell=out["design_effect"]["design_cell"]["effective_n"],
        effective_n_family=out["design_effect"]["family"]["effective_n"],
        mundlak_within_beta=mun_cell["beta_within"],
        mundlak_within_p=mun_cell["p_within"],
        mundlak_between_beta=mun_cell["beta_between"],
        mundlak_between_p=mun_cell["p_between"],
        oos_r2_cell=oos_cell, oos_r2_family=oos_fam,
        oos_r2_cell_median_fold=hold["leave_one_design_cell_out"]["r2_oos_median_fold"],
        oos_r2_family_median_fold=hold["leave_one_family_out"]["r2_oos_median_fold"],
        oos_frac_folds_beating_baseline_cell=hold["leave_one_design_cell_out"][
            "frac_folds_r2_positive"],
        oos_frac_folds_beating_baseline_family=hold["leave_one_family_out"][
            "frac_folds_r2_positive"],
        cr1_se_design_cell=cr["se_cr1"][1],
        cr1_p_design_cell_t5=float(2.0 * stats.t.sf(
            abs(float(cr["beta"][1]) / float(cr["se_cr1"][1])), cr["G"] - 1)),
        cr1_se_family=cr_fam["se_cr1"][1],
        cr1_p_family_t11=float(2.0 * stats.t.sf(
            abs(float(cr_fam["beta"][1]) / float(cr_fam["se_cr1"][1])), cr_fam["G"] - 1)),
        cr1_beta_DG=round(float(cr["beta"][1]), 4),
        n_design_cells=int(len(set(cell.tolist()))),
        largest_cell_share=round(float(np.max([int((cell == c).sum())
                                               for c in sorted(set(cell.tolist()))])) / 204, 4),
        statement=("association, not prediction"),
    )

    for fname, payload in (
            ("pr_stats_within_group.json", dict(provenance=prov, **within_block)),
            ("pr_stats_mixed_effects.json", dict(provenance=prov, **mixed)),
            ("pr_stats_cluster_bootstrap.json", dict(provenance=prov, **bc)),
            ("pr_stats_holdout.json", dict(provenance=prov, **hold)),
            ("pr_stats_hardened.json", out)):
        p = os.path.join(OUT_DIR, fname)
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("wrote %s" % os.path.relpath(p, ROOT).replace("\\", "/"))

    print("\n[verdict] pooled r=%+.4f but within-family r=%+.4f, within-cell r=%+.4f;"
          % (r_pooled, within_fam_r, within_cell_r))
    print("          mixed beta=%+.4f (se %.4f), ICC_random=%.3f,"
          % (mixed["M4_random_intercepts_dataset_model_config"]["beta_DG"],
             mixed["M4_random_intercepts_dataset_model_config"]["se_DG"], icc_random))
    print("          Mundlak within beta=%+.4f (p=%.3g) vs between beta=%+.4f (p=%.3g);"
          % (mun_cell["beta_within"], mun_cell["p_within"],
             mun_cell["beta_between"], mun_cell["p_between"]))
    print("          held-out R^2 = %+.4f (cells) / %+.4f (families) vs in-sample %.4f"
          % (oos_cell, oos_fam, hold["in_sample"]["r2"]))
    print("          CR1 SLOPE SE by design cell = %.4f (x%.2f the OLS SE), p(t5)=%.4g"
          % (cr["se_cr1"][1], cr["se_cr1"][1] / cr["se_ols"][1],
             out["verdict"]["cr1_p_design_cell_t5"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

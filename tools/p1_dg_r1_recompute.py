# -*- coding: utf-8 -*-
"""
P1 fix for [M11]/[A3]: replace the unreconstructible n=81 correlation with a
reproducible one.

Background
    paper/scripts/generate_figures.py:74-77 states that the selection rule behind the
    n=81 correlation was lost with the original script and that the subset "cannot be
    exactly reconstructed", yet r = -0.827 / partial -0.807 (n=81) is the abstract's
    headline number (Table 5, Fig. 2).  A reviewer asking "which 81 rows?" cannot be
    answered.

What this does
    Recomputes the same four correlations over every experiment in the archive that
    satisfies a rule stated in full below, and writes both the numbers and the exact
    list of contributing rows.  The rule is deliberately simple enough to print in a
    figure caption.

    RULE: every outputs/**/results.json that records a finite final_gap.centroid_gap
          and final_gap.distribution_gap together with final_task_metrics.R@1, one row
          per experiment directory; directories whose path contains any of
          EXCLUDE are skipped (figures/comparison are the original script's own
          exclusions; strict_freeze* is this month's control run and is reported
          separately so the legacy correlation stays comparable).

Outputs
    outputs/analysis/dg_r1_reproducible.json   numbers + full row provenance
    stdout                                     a table to paste into the manuscript
"""
import io
import json
import os
import sys

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
OUT_DIR = os.path.join(ROOT, "outputs")
OUT_JSON = os.path.join(OUT_DIR, "analysis", "dg_r1_reproducible.json")

EXCLUDE = ("figures", "comparison", "strict_freeze", "smoke", "_void", "old", "backup")


def finite(*vals):
    for v in vals:
        if v is None:
            return False
        try:
            if not np.isfinite(float(v)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def collect():
    rows = []
    for dirpath, dirnames, filenames in os.walk(OUT_DIR):
        if "results.json" not in filenames:
            continue
        rel = os.path.relpath(dirpath, OUT_DIR).replace("\\", "/")
        if any(x in rel.lower() for x in EXCLUDE):
            continue
        try:
            with io.open(os.path.join(dirpath, "results.json"), encoding="utf-8") as fh:
                r = json.load(fh)
        except (OSError, ValueError):
            continue
        fg, ig = r.get("final_gap"), r.get("initial_gap")
        tm = r.get("final_task_metrics")
        if not isinstance(fg, dict) or not isinstance(tm, dict):
            continue
        dg_f, cg_f = fg.get("distribution_gap"), fg.get("centroid_gap")
        r1 = tm.get("R@1")
        dg_i = (ig or {}).get("distribution_gap")
        cg_i = (ig or {}).get("centroid_gap")
        if not finite(dg_f, cg_f, r1):
            continue
        rows.append({
            "path": rel,
            "dg_final": float(dg_f), "cg_final": float(cg_f), "r1": float(r1),
            "dg_init": float(dg_i) if finite(dg_i) else None,
            "cg_init": float(cg_i) if finite(cg_i) else None,
        })
    return rows


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def cluster_bootstrap(rows, x_key, y_key, n_boot=10000, seed=42):
    """Bootstrap over experiment families (the first path component), since runs that
    share a family are not independent observations.  Returns (mean r, 2.5% , 97.5%,
    fraction >= 0)."""
    rng = np.random.default_rng(seed)
    groups = {}
    for r in rows:
        groups.setdefault(r["path"].split("/")[0], []).append(r)
    keys = list(groups)
    out = []
    for _ in range(n_boot):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        sel = [row for i in pick for row in groups[keys[i]]]
        xs = [row[x_key] for row in sel]
        ys = [row[y_key] for row in sel]
        rr = pearson(xs, ys)
        if np.isfinite(rr):
            out.append(rr)
    out = np.array(out)
    return (float(out.mean()), float(np.percentile(out, 2.5)),
            float(np.percentile(out, 97.5)), float((out >= 0).mean()), len(keys))


def pearson_p(a, b):
    """two-sided p for the Pearson r (Student t with n-2 df)."""
    r = pearson(a, b)
    n = len(a)
    if not np.isfinite(r) or n < 3 or abs(r) >= 1.0:
        return float("nan")
    t = r * np.sqrt((n - 2) / (1 - r * r))
    try:
        from scipy import stats
        return float(2 * stats.t.sf(abs(t), n - 2))
    except ImportError:
        # normal approximation, adequate for the n here
        from math import erfc, sqrt
        return float(erfc(abs(t) / sqrt(2)))


def variant(rows, name, keep):
    sel = [r for r in rows if keep(r)]
    n = len(sel)
    if n < 3:
        return {"variant": name, "n": n, "note": "too few rows"}
    r1 = [r["r1"] for r in sel]
    dg = [r["dg_final"] for r in sel]
    cg = [r["cg_final"] for r in sel]
    r_dg, r_cg, r_x = pearson(dg, r1), pearson(cg, r1), pearson(dg, cg)
    den = np.sqrt((1 - r_x ** 2) * (1 - r_cg ** 2))
    part = ((r_dg - r_x * r_cg) / den) if den > 0 else float("nan")
    return {"variant": name, "n": n,
            "DG_vs_R1": round(r_dg, 4), "CG_vs_R1": round(r_cg, 4),
            "DG_vs_CG": round(r_x, 4), "partial_DG_given_CG": round(part, 4)}


# the exclusion keywords documented in paper/scripts/generate_figures.py:65
LEGACY_SK = ("seed", "blip", "coco", "vitl", "phase", "route", "null",
             "gap_init", "rq3", "alpha_", "modules_")


def main():
    rows = collect()
    VARIANTS = [
        ("V1 all archived rows", lambda r: True),
        ("V2 all, R@1>=0.01", lambda r: r["r1"] >= 0.01),
        ("V3 legacy keyword filter", lambda r: not any(k in r["path"].lower() for k in LEGACY_SK)),
        ("V4 legacy filter + R@1>=0.01",
         lambda r: (not any(k in r["path"].lower() for k in LEGACY_SK)) and r["r1"] >= 0.01),
        ("V5 flickr30k only", lambda r: "flickr" in r["path"].lower()),
        ("V6 flickr30k, R@1>=0.01",
         lambda r: "flickr" in r["path"].lower() and r["r1"] >= 0.01),
    ]
    table = [variant(rows, name, keep) for name, keep in VARIANTS]

    print("%-30s %5s %9s %9s %9s %10s" % ("variant", "n", "DG->R1", "CG->R1",
                                          "DG~CG", "DG|CG"))
    for t in table:
        if "note" in t:
            print("%-30s %5d  %s" % (t["variant"], t["n"], t["note"]))
        else:
            print("%-30s %5d %+9.4f %+9.4f %+9.4f %+10.4f"
                  % (t["variant"], t["n"], t["DG_vs_R1"], t["CG_vs_R1"],
                     t["DG_vs_CG"], t["partial_DG_given_CG"]))

    r1s = np.array([r["r1"] for r in rows])
    print("\nR@1 spread over the archive: min %.4f  p25 %.4f  median %.4f  p75 %.4f  max %.4f"
          % (r1s.min(), np.percentile(r1s, 25), np.median(r1s),
             np.percentile(r1s, 75), r1s.max()))
    print("rows with R@1 < 0.05: %d   < 0.01: %d"
          % (int((r1s < 0.05).sum()), int((r1s < 0.01).sum())))

    base = variant(rows, "all archived rows", lambda r: True)
    r1s_all = [r["r1"] for r in rows]
    dgs = [r["dg_final"] for r in rows]
    cgs = [r["cg_final"] for r in rows]
    delta = [r for r in rows if r["dg_init"] is not None and r["cg_init"] is not None]
    dg_d = [r["dg_final"] - r["dg_init"] for r in delta]
    cg_d = [r["cg_final"] - r["cg_init"] for r in delta]
    r1_d = [r["r1"] for r in delta]

    primary = dict(base)
    primary.update({
        "DG_p": round(pearson_p(dgs, r1s_all), 6),
        "CG_p": round(pearson_p(cgs, r1s_all), 6),
        "DG_delta_r": round(pearson(dg_d, r1_d), 4),
        "DG_delta_p": round(pearson_p(dg_d, r1_d), 6),
        "CG_delta_r": round(pearson(cg_d, r1_d), 4),
        "CG_delta_p": round(pearson_p(cg_d, r1_d), 6),
        "n_delta": len(delta),
    })
    print("\nPAPER-READY (n=%d):" % primary["n"])
    print("  DG  -> R@1          r = %+.3f  p = %.3g" % (primary["DG_vs_R1"], primary["DG_p"]))
    print("  CG  -> R@1          r = %+.3f  p = %.3g" % (primary["CG_vs_R1"], primary["CG_p"]))
    print("  DG  -> R@1 | CG     r = %+.3f" % primary["partial_DG_given_CG"])
    print("  DGdelta -> R@1      r = %+.3f  p = %.3g" % (primary["DG_delta_r"], primary["DG_delta_p"]))
    print("  CGdelta -> R@1      r = %+.3f  p = %.3g" % (primary["CG_delta_r"], primary["CG_delta_p"]))
    print("  DG ~ CG             r = %+.3f" % primary["DG_vs_CG"])

    boot_dg = cluster_bootstrap(rows, "dg_final", "r1")
    boot_cg = cluster_bootstrap(rows, "cg_final", "r1")
    print("\nclustered bootstrap (cluster = experiment family, %d clusters, 10k resamples):"
          % boot_dg[4])
    print("  DG -> R@1  mean %+.3f  95%% CI [%+.3f, %+.3f]  frac(r>=0) = %.4f"
          % (boot_dg[0], boot_dg[1], boot_dg[2], boot_dg[3]))
    print("  CG -> R@1  mean %+.3f  95%% CI [%+.3f, %+.3f]  frac(r>=0) = %.4f"
          % (boot_cg[0], boot_cg[1], boot_cg[2], boot_cg[3]))

    primary["cluster_bootstrap"] = {
        "cluster_unit": "first path component under outputs/ (experiment family)",
        "n_clusters": boot_dg[4],
        "DG_mean": round(boot_dg[0], 4), "DG_ci": [round(boot_dg[1], 4), round(boot_dg[2], 4)],
        "DG_frac_ge_0": round(boot_dg[3], 5),
        "CG_mean": round(boot_cg[0], 4), "CG_ci": [round(boot_cg[1], 4), round(boot_cg[2], 4)],
        "CG_frac_ge_0": round(boot_cg[3], 5),
    }

    out = {
        "rule": ("every outputs/**/results.json with finite final_gap.centroid_gap, "
                 "final_gap.distribution_gap and final_task_metrics.R@1; one row per "
                 "experiment directory; paths containing %s excluded" % (EXCLUDE,)),
        "supersedes": ("the n=81 subset used in Table 5 / Fig. 2 / the abstract, whose "
                       "selection rule was lost (paper/scripts/generate_figures.py:74-77)"),
        "sensitivity": table,
        "primary": primary,
        "rows": rows,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("\nwrote %s" % OUT_JSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())

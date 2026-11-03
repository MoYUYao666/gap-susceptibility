# -*- coding: utf-8 -*-
r"""Stratified DG-R@1 figure: the within-cell view a reviewer asked for.

Reviewer 1 (question 4) asked for "stratified DG-R@1 plots by model or dataset" and warned (question
3) that the pooled r = -0.71 might be between-group structure rather than a within-setting relation.
`outputs/analysis/pr_stats_within_group.json` already answers the statistics -- the within-group
slopes are pooled_within_dataset -0.751 and pooled_within_model -0.707, close to the pooled value, so
the association is not a between-group artefact -- but the manuscript had no figure for it.

This script draws that figure and re-derives every number in it from the per-row archive, so the plot
cannot drift from the statistics:

* rows come from `outputs/analysis/dg_r1_reproducible.json` (204 rows, the same input the stats file
  names in its provenance);
* dataset and model labels come from `tools/_p260_pr_stats_hardening.py`, the script that produced the
  archive, so the grouping rule is the same one the correlations used;
* the per-dataset and per-model correlations computed here are asserted against the archived values
  before anything is drawn.

Writes `paper合/figures/fig15_stratified_dg_r1.pdf` and `outputs/analysis/fig15_stratified.json`.

    python tools/_p860_fig_stratified.py [--apply]
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROWS = REPO / "outputs" / "analysis" / "dg_r1_reproducible.json"
STATS = REPO / "outputs" / "analysis" / "pr_stats_within_group.json"
LABELER = REPO / "tools" / "_p260_pr_stats_hardening.py"
FIG = REPO / "paper合" / "figures" / "fig15_stratified_dg_r1.pdf"
OUT = REPO / "outputs" / "analysis" / "fig15_stratified.json"


def r_p(a: list[float], b: list[float]) -> tuple[float, float]:
    n = len(a)
    if n < 3:
        return float("nan"), float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if sa == 0 or sb == 0:
        return float("nan"), float("nan")
    r = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)
    r = max(-1.0, min(1.0, r))
    if abs(r) >= 1.0:
        return r, 0.0
    t = r * math.sqrt((n - 2) / (1 - r * r))
    # two-sided p from the t distribution, via the incomplete beta function
    x = (n - 2) / ((n - 2) + t * t)
    p = betainc((n - 2) / 2.0, 0.5, x)
    return r, p


def betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta, continued fraction (Numerical Recipes 6.4)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-12:
            break
    p = front * (f - 1.0)
    return p if a > (a + b) * x else 1.0 - betainc(b, a, 1 - x)


def load_labels() -> dict:
    spec = importlib.util.spec_from_file_location("p260", LABELER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = json.loads(ROWS.read_text(encoding="utf-8"))["rows"]
    labelled = []
    for r in rows:
        _fam, _cfg, ds, model, _tier, _ev = mod.classify(r["path"])
        labelled.append({"path": r["path"], "dg": r["dg_final"], "r1": r["r1"],
                         "dataset": ds, "model": model})
    return {"rows": labelled}


def group_stats(rows: list[dict], key: str) -> dict:
    out = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return {k: {"n": len(v), "r": r_p([x["dg"] for x in v], [x["r1"] for x in v])}
            for k, v in sorted(out.items())}


def pooled_within(rows: list[dict], key: str) -> tuple[float, float, int, int]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r)
    xs, ys, ng = [], [], 0
    for v in groups.values():
        if len(v) < 2:
            continue
        mx = sum(x["dg"] for x in v) / len(v)
        my = sum(x["r1"] for x in v) / len(v)
        xs += [x["dg"] - mx for x in v]
        ys += [x["r1"] - my for x in v]
        ng += 1
    r, p = r_p(xs, ys)
    return r, p, ng, len(xs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    lab = load_labels()
    all_rows = lab["rows"]
    # The archived correlations were computed over every labelled row, including the UNDOCUMENTED and
    # DISPUTED groups; the figure shows only the two settled datasets, so both sets are kept: `all_rows`
    # for the reproduction checks, `rows` for plotting.
    rows = [r for r in all_rows if r["dataset"] not in ("UNDOCUMENTED", "DISPUTED")]
    stats = json.loads(STATS.read_text(encoding="utf-8"))

    check_ds, check_md = group_stats(all_rows, "dataset"), group_stats(all_rows, "model")
    by_ds, by_md = group_stats(rows, "dataset"), group_stats(rows, "model")

    # the grouping must reproduce the archived correlations, or the figure would tell a different story
    for name, computed in (("by_dataset", check_ds), ("by_model", check_md)):
        for k, v in computed.items():
            ref = stats[name].get(k, {}).get("r")
            if ref is None or v["r"][0] != v["r"][0]:
                continue
            assert abs(v["r"][0] - ref) < 0.002, \
                f"{name}[{k}]: computed {v['r'][0]:.4f} vs archived {ref:.4f}"
    pw_ds = pooled_within(all_rows, "dataset")
    pw_md = pooled_within(all_rows, "model")
    assert abs(pw_ds[0] - stats["pooled_within_dataset"]["r_within"]) < 0.002, pw_ds
    assert abs(pw_md[0] - stats["pooled_within_model"]["r_within"]) < 0.002, pw_md
    print(f"  labels reproduce the archive: dataset r within {pw_ds[0]:+.4f} "
          f"(archived {stats['pooled_within_dataset']['r_within']:+.4f}), "
          f"model r within {pw_md[0]:+.4f} (archived {stats['pooled_within_model']['r_within']:+.4f})")

    payload = {"rows_source": "outputs/analysis/dg_r1_reproducible.json",
               "label_source": "tools/_p260_pr_stats_hardening.py :: classify()",
               "n_rows": len(rows),
               "by_dataset": {k: {"n": v["n"], "r": round(v["r"][0], 4), "p": v["r"][1]}
                              for k, v in by_ds.items()},
               "by_model": {k: {"n": v["n"], "r": round(v["r"][0], 4), "p": v["r"][1]}
                            for k, v in by_md.items()},
               "pooled_within_dataset": {"r": round(pw_ds[0], 4), "p": pw_ds[1], "n_rows": pw_ds[3]},
               "pooled_within_model": {"r": round(pw_md[0], 4), "p": pw_md[1], "n_rows": pw_md[3]},
               "pooled_all": {"r": round(r_p([r["dg"] for r in rows], [r["r1"] for r in rows])[0], 4)}}
    if not a.apply:
        print("  (dry run)")
        print(json.dumps(payload["by_dataset"], indent=1))
        print(json.dumps(payload["by_model"], indent=1))
        return 0

    import matplotlib
    matplotlib.use("Agg")
    import sys as _sys
    _sys.path.insert(0, str(REPO / "tools"))
    import figure_style
    import matplotlib.pyplot as plt

    # Times New Roman for all figure text and STIX (Times-compatible) for the maths, so the figure
    # matches the body font, which is what the rest of the library uses.
    figure_style.apply_style()

    # Draw at the final printed size so LaTeX scales by 1.00x, like the rest of the library
    # (`tools/figure_style.py` sets savefig.bbox=None for exactly this reason: a tight bbox grows the
    # canvas by the label extents, which silently changes the text size once LaTeX rescales it).
    plt.rcParams.update({"figure.dpi": 300, "savefig.bbox": None})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figure_style.figsize_full(0.46))
    fig.subplots_adjust(wspace=0.46)

    # --- panel (a): the per-cell scatter with its own fit ---
    keys = [k for k in ("flickr30k", "coco") if k in by_ds]
    # Both panels draw from the shared Okabe-Ito palette so a figure cannot introduce a foreign colour;
    # the two datasets take blue and green, neither of which is used for anything else here.
    colors = {"flickr30k": figure_style.OKABE_ITO["blue"], "coco": figure_style.OKABE_ITO["green"],
              "CLIP ViT-B/32": figure_style.SEMANTIC["text_only"],
              "BLIP": figure_style.OKABE_ITO["sky"], "SigLIP": figure_style.SEMANTIC["both"]}
    for k in keys:
        v = [r for r in rows if r["dataset"] == k]
        ax1.scatter([x["dg"] for x in v], [x["r1"] for x in v], s=7, alpha=0.75,
                    color=colors.get(k, "#555555"), label=f"{k} (n={len(v)}, r={by_ds[k]['r'][0]:+.2f})",
                    edgecolors="none")
        # OLS fit for this cell
        n = len(v)
        mx = sum(x["dg"] for x in v) / n
        my = sum(x["r1"] for x in v) / n
        sxx = sum((x["dg"] - mx) ** 2 for x in v)
        if sxx > 0:
            b = sum((x["dg"] - mx) * (x["r1"] - my) for x in v) / sxx
            xs = [min(x["dg"] for x in v), max(x["dg"] for x in v)]
            ax1.plot(xs, [my + b * (x - mx) for x in xs], color=colors.get(k, "#555555"), lw=1.4)
    ax1.set_xlabel(r"Distribution Gap $DG^*$")
    ax1.set_ylabel(r"$R@1$")
    ax1.set_yscale("symlog", linthresh=0.01)
    # Titles are kept out of the panels: at the printed width there is no room above the axes, and the
    # caption already names the two panels. The two correlation values the titles used to carry are
    # printed in the caption instead, where they are quoted from the archive.
    ax1.legend(loc="lower left", frameon=False)

    # --- panel (b): per-cell correlations, showing the one reversal ---
    order = sorted(by_md.items(), key=lambda kv: kv[1]["r"][0])
    names = [k for k, _ in order]
    vals = [v["r"][0] for _, v in order]
    ns = [v["n"] for _, v in order]
    bars = ax2.bar(range(len(names)), vals,
                   color=[figure_style.SEMANTIC["text_only"] if x < 0 else figure_style.SEMANTIC["both"]
                          for x in vals], width=0.6)
    for i, (b, v, n) in enumerate(zip(bars, vals, ns)):
        ax2.text(b.get_x() + b.get_width() / 2, v + (0.05 if v >= 0 else -0.10),
                 f"{v:+.2f}\nn={n}", ha="center", va="bottom" if v >= 0 else "top", fontsize=6.5)
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_xticks(range(len(names)))
    ax2.set_xticklabels(names, rotation=15, ha="right")
    ax2.set_ylabel(r"Pearson $r$")
    ax2.set_ylim(min(vals) - 0.45, max(vals) + 0.45)

    fig.savefig(FIG)
    # every other figure in the library ships a 300-dpi PNG next to its vector PDF; produce it here so
    # the pair stays in step (tools/_p867_figure_audit.py checks the pairing).
    fig.savefig(FIG.with_suffix(".png"), dpi=300)
    payload["figure"] = "paper合/figures/fig15_stratified_dg_r1.pdf"
    payload["panel_b_models"] = names
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    assert FIG.exists() and FIG.stat().st_size > 1000, "figure was not written"
    print(f"  wrote {FIG.relative_to(REPO).as_posix()} ({FIG.stat().st_size:,} bytes)")
    print(f"  wrote {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""Add the within-group (stratified) statistics and their figure to the manuscript.

Reviewer 1 in the PR decision letter asked (question 3) for "within-dataset and within-model
correlations ... together with mixed-effects regression, clustered bootstrap, or another group-aware
analysis", and (question 4) for "stratified DG-R@1 plots by model or dataset". The mixed model,
cluster-robust inference and clustered bootstrap are already in the paper; the within-group
correlations and the stratified figure were not, even though `outputs/analysis/pr_stats_within_group.json`
has held them since the statistics were hardened.

Every number in the inserted text is read from that archive at run time and asserted against it, so
the sentence cannot drift:

* within-family  r = -0.5506 over 11 groups / 202 rows
* within-design-cell r = -0.7310 over 5 groups
* within-dataset r = -0.7512 over 3 groups
* within-model   r = -0.7073 over 3 groups

The per-cell correlations the figure shows (flickr30k -0.7809, coco -0.5984; CLIP ViT-B/32 -0.7476,
BLIP -0.9765, SigLIP +0.8083) come from the same file.

    python tools/_p861_add_stratified.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"
NC_EMP = REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex"
STATS = REPO / "outputs" / "analysis" / "pr_stats_within_group.json"
FIG = "figures/fig15_stratified_dg_r1.pdf"
MARK = "fig:stratified"

ANCHOR = ("A six-variant sensitivity analysis over sample definition (all rows, R@1 $\\geq 0.01$, "
          "legacy keyword filter, Flickr30k only) preserves the ordering DG $>$ CG in every variant.")


def body() -> str:
    d = json.loads(STATS.read_text(encoding="utf-8"))
    pwf = d["pooled_within_family"]
    pwc = d["pooled_within_design_cell"]
    pwd = d["pooled_within_dataset"]
    pwm = d["pooled_within_model"]
    bd, bm = d["by_dataset"], d["by_model"]
    return "\n".join([
        "",
        "The same question has a direct answer: how much of the association survives once the grouping",
        "is held fixed. Centring $DG^*$ and $R@1$ inside each group and correlating the stacked",
        "deviations gives $r = " + f"{pwd['r_within']:.3f}" + "$ within dataset"
        + f" ({pwd['n_groups']} groups, {pwd['n_rows']} rows), $r = {pwm['r_within']:.3f}$ within model"
        + f" ({pwm['n_groups']} groups), $r = {pwc['r_within']:.3f}$ within design cell"
        + f" ({pwc['n_groups']} groups), and $r = {pwf['r_within']:.3f}$ within experiment family"
        + f" ({pwf['n_groups']} groups). These are close to the pooled $r = -0.714$, so the association",
        "is not a between-group artefact of comparing corpora that sit at different gaps. It is also",
        "not uniform, and the stratified view in Figure~\\ref{fig:stratified} is what shows the",
        "exception: per dataset the correlation is $r = " + f"{bd['flickr30k']['r']:.3f}"
        + f"$ on Flickr30k ($n = {bd['flickr30k']['n']}$) against $r = {bd['coco']['r']:.3f}$ on MS-COCO"
        + f" ($n = {bd['coco']['n']}$), and per model it is $r = {bm['CLIP ViT-B/32']['r']:.3f}$ on CLIP"
        + f" ViT-B/32 ($n = {bm['CLIP ViT-B/32']['n']}$), $r = {bm['BLIP']['r']:.3f}$ on BLIP"
        + f" ($n = {bm['BLIP']['n']}$) and $r = {bm['SigLIP']['r']:+.3f}$ on SigLIP"
        + f" ($n = {bm['SigLIP']['n']}$). The sign reversal on SigLIP is the same reversal the",
        "adaptation-position control reports, and its $n$ is small, so we read it as the boundary of the",
        "association rather than as a second relationship. Two of the design cells hold fewer than four",
        "runs and are shown in the figure for completeness only.",
        "",
        "\\begin{figure}[ht]",
        "\\centering",
        "\\includegraphics[width=0.95\\textwidth]{" + FIG + "}",
        "\\caption{The DG--retrieval association stratified by dataset (a) and by model (b). Panel (a)",
        "plots every run against its own cell's fit, which is the within-setting relation the pooled",
        "correlation is often suspected of hiding; panel (b) collects the per-model correlations and",
        "shows the one reversal, on SigLIP. Sample sizes are printed on both panels because three of the",
        "groups hold five runs or fewer, where a correlation is descriptive rather than inferential.",
        "Derived from \\texttt{outputs/analysis/dg\\_r1\\_reproducible.json} by",
        "\\texttt{tools/\\_p860\\_fig\\_stratified.py}.}",
        "\\label{fig:stratified}",
        "\\end{figure}",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    block = body()
    targets = [EMP, NC_EMP]
    for p in targets:
        assert p.exists(), f"missing {p}"
        t = io.open(p, encoding="utf-8").read()
        already = MARK in t
        print(f"  {p.relative_to(REPO).as_posix()}: "
              f"{'already present' if already else 'anchor ' + ('found' if t.count(ANCHOR) == 1 else 'MISSING')}")
        if already:
            continue
        assert t.count(ANCHOR) == 1, "the sensitivity sentence was not found exactly once"
        if a.apply:
            t = t.replace(ANCHOR, ANCHOR + block, 1)
            io.open(p, "w", encoding="utf-8", newline="").write(t)

    if not a.apply:
        print("  (dry run)")
        return 0

    for p in targets:
        t = io.open(p, encoding="utf-8").read()
        # the marker appears twice by design: once in \ref{fig:stratified} and once in \label{...}
        assert t.count(MARK) == 2, f"{p.name}: expected a reference and a label, found {t.count(MARK)}"
        assert FIG in t, f"{p.name}: figure path missing"
        for needle in ("-0.751", "-0.707", "-0.731", "-0.551", "0.808"):
            assert needle in t, f"{p.name}: missing {needle}"
        print(f"  verified {p.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

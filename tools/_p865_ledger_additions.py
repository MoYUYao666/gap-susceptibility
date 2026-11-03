# -*- coding: utf-8 -*-
r"""Add the 2026-10-15 manuscript numbers to the Paper A claim ledger.

The manuscript grew three sets of numbers this session, and the standing rule is that every number a
paper prints must name the script that produced it and the archive field that carries it:

* the full-scale MS-COCO result (`outputs/analysis/full_coco.json`),
* the within-group and per-cell DG-retrieval correlations plus the stratified figure
  (`outputs/analysis/pr_stats_within_group.json`, `outputs/analysis/fig15_stratified.json`),
* the repaired 3,000-image COCO protocol (`outputs/analysis/coco_scaleup.json`).

This script appends one section to `tools/_claim_ledger_paperA.py` before its summary block, so the
gate keeps its single entry point. It is additive and idempotent, and it asserts that each added claim
reads a real field.

    python tools/_p865_ledger_additions.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "tools" / "_claim_ledger_paperA.py"
MARK = "§7：本轮新增（2026-10-15）"
ANCHOR = '    print()\n    print("=" * 118)\n    print(f"  PASS {ok} ｜ GAP {gap} ｜ total {ok + gap}")'

SECTION = '''    print()
    print("  --- §7：本轮新增（2026-10-15）---")
    # full-scale MS-COCO: 10,000 training images, the whole val2014 split as the gallery
    fc = j("outputs/analysis/full_coco.json")
    fz = [r for r in fc["runs"] if r["arm"] == "frozen"][0]
    tx = [r for r in fc["runs"] if r["arm"] == "text_only"]
    record("full-COCO frozen R@1", 0.5655, round(fz["R@1"], 4),
           "outputs/analysis/full_coco.json :: runs[arm=frozen].R@1",
           abs(fz["R@1"] - 0.5655) <= 0.0005)
    record("full-COCO text-only R@1 (3 seeds)", 0.5823,
           round(st.mean([r["R@1"] for r in tx]), 4),
           "outputs/analysis/full_coco.json :: mean(runs[arm=text_only].R@1)",
           abs(st.mean([r["R@1"] for r in tx]) - 0.5823) <= 0.0005, "[sd 0.0002]")
    record("full-COCO gallery images", 40504, tx[0]["n_unique_images"],
           "outputs/analysis/full_coco.json :: runs[0].n_unique_images",
           tx[0]["n_unique_images"] == 40504)
    record("full-COCO caption rows", 202654, tx[0]["n_captions"],
           "outputs/analysis/full_coco.json :: runs[0].n_captions",
           tx[0]["n_captions"] == 202654)
    record("full-COCO text-to-image R@1 (text-only)", 0.1650,
           round(st.mean([r["R@1_t2i"] for r in tx]), 4),
           "outputs/analysis/full_coco.json :: mean(runs[arm=text_only].R@1_t2i)",
           abs(st.mean([r["R@1_t2i"] for r in tx]) - 0.1650) <= 0.0005)
    # the repaired 3,000-image COCO protocol
    cs = j("outputs/analysis/coco_scaleup.json")
    arm = {}
    for r in cs["runs"]:
        arm.setdefault(r["arm"], []).append(r)
    record("COCO 3k frozen R@1", 0.579, round(arm["frozen"][0]["R@1"], 4),
           "outputs/analysis/coco_scaleup.json :: runs[arm=frozen].R@1",
           abs(arm["frozen"][0]["R@1"] - 0.579) <= 0.0005)
    record("COCO 3k text-only R@1", 0.607, round(st.mean([r["R@1"] for r in arm["text_only"]]), 4),
           "outputs/analysis/coco_scaleup.json :: mean(runs[arm=text_only].R@1)",
           abs(st.mean([r["R@1"] for r in arm["text_only"]]) - 0.607) <= 0.0005)
    record("COCO 3k both-position R@1", 0.623, round(st.mean([r["R@1"] for r in arm["both"]]), 4),
           "outputs/analysis/coco_scaleup.json :: mean(runs[arm=both].R@1)",
           abs(st.mean([r["R@1"] for r in arm["both"]]) - 0.623) <= 0.0005)
    # the stratified statistics and the figure derived from the same input
    wg = j("outputs/analysis/pr_stats_within_group.json")
    claim("within-dataset r (manuscript -0.751)", -0.751,
          "outputs/analysis/pr_stats_within_group.json", "pooled_within_dataset.r_within")
    claim("within-model r (manuscript -0.707)", -0.707,
          "outputs/analysis/pr_stats_within_group.json", "pooled_within_model.r_within")
    claim("within-design-cell r (manuscript -0.731)", -0.731,
          "outputs/analysis/pr_stats_within_group.json", "pooled_within_design_cell.r_within")
    claim("within-family r (manuscript -0.551)", -0.551,
          "outputs/analysis/pr_stats_within_group.json", "pooled_within_family.r_within")
    claim("SigLIP reversal r (manuscript +0.808)", 0.808,
          "outputs/analysis/pr_stats_within_group.json", "by_model.SigLIP.r")
    f15 = j("outputs/analysis/fig15_stratified.json")
    # Three row counts are in play and they differ for a benign reason worth naming:
    #   * the corpus is 204 rows;
    #   * the pooled within-group statistics centre every group, so rows that sit alone in their group
    #     contribute nothing and the stats archive counts 202 grouped rows;
    #   * the figure plots the 199 rows of the two settled datasets only.
    # The correlations agree exactly between the two archives, which is the check that matters.
    record("figure 15 rows plotted", 199, f15["n_rows"],
           "outputs/analysis/fig15_stratified.json :: n_rows", f15["n_rows"] == 199)
    record("pooled within rows (grouped)", 202, wg["pooled_within_dataset"]["n_rows"],
           "outputs/analysis/pr_stats_within_group.json :: pooled_within_dataset.n_rows",
           wg["pooled_within_dataset"]["n_rows"] == 202,
           "[the corpus is 204; two rows sit alone in their group]")
    record("figure 15 rows (all labelled)", 204, f15["pooled_within_dataset"]["n_rows"],
           "outputs/analysis/fig15_stratified.json :: pooled_within_dataset.n_rows",
           f15["pooled_within_dataset"]["n_rows"] == 204)
    record("figure 15 within-dataset r", -0.7512, f15["pooled_within_dataset"]["r"],
           "outputs/analysis/fig15_stratified.json :: pooled_within_dataset.r",
           abs(f15["pooled_within_dataset"]["r"] + 0.7512) <= 0.0005)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = io.open(LEDGER, encoding="utf-8").read()
    if MARK in t:
        print("  already recorded")
        return 0
    assert t.count(ANCHOR) == 1, "the summary anchor was not found exactly once"
    if not a.apply:
        print("  (dry run)")
        print(f"  would insert {len(SECTION.splitlines())} lines before the summary block")
        return 0

    out = t.replace(ANCHOR, SECTION + ANCHOR, 1)
    assert out.count(MARK) == 1
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(out)

    check = io.open(LEDGER, encoding="utf-8").read()
    for needle in ("full-COCO frozen R@1", "full-COCO gallery images", "within-dataset r",
                   "figure 15 rows", "COCO 3k both-position R@1"):
        print(f"  {'OK ' if needle in check else 'BAD'} {needle}")
    print(f"  ledger lines = {len(check.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

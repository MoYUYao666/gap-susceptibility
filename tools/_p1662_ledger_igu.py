#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1662_ledger_igu.py -- register every official-implementation comparison number printed in
the supplement (S41 subsection app:igucompare) in tools/_p1637_p3_reproduce_all.py.

Idempotent: skips if the S41c marker is present.
"""
import io
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = ROOT / "tools/_p1637_p3_reproduce_all.py"
MARKER = "# --- S41c: official-implementation comparison"
ANCHOR = "# --- S29: second-environment reproducibility"

BLOCK = r'''# --- S41c: official-implementation comparison (S41 subsection, 2026-10-25) --------------
# Every value is a field of outputs/analysis/p3_official_vs_reimpl.json (sha256 4698a6e7...),
# outputs/analysis/p3_official_igu_run.json (sha256 8f4546ed...) or
# outputs/analysis/p3_official_igu_replicates.json.  The single-seed arm readings (182.5 / 333.0)
# are deliberately NOT registered: they are not printed as the comparison (audit_check.py keeps
# them out of the S41 slice).
_IGU = ANA + "/p3_official_vs_reimpl.json"
_IGU_RUN = ANA + "/p3_official_igu_run.json"
_IGU_REP = ANA + "/p3_official_igu_replicates.json"
calc("s41c-n-runs", "S41", "supplementary.tex tab:igucompare 'six trained arms'",
     "6", _IGU_RUN, "runs (length)", "number of trained arms in the six-arm consolidation",
     6.0, fn=lambda: float(len(_load(_IGU_RUN)["runs"])), tol=T_ABS)
add("s41c-gap", "S41", "supplementary.tex tab:igucompare 'paired gap -59.5'",
    "-59.5", _IGU, "overall.mean_gap_delta_E", "archived paired mean gap", -59.5, tol=T_EXACT)
add("s41c-ci-lo", "S41", "supplementary.tex '95% CI [-150.5,...]'",
    "-150.5", _IGU, "overall.ci95.0", "archived 2.5th percentile", -150.5, tol=T_EXACT)
add("s41c-ci-hi", "S41", "supplementary.tex '95% CI [...,-8.0]'",
    "-8.0", _IGU, "overall.ci95.1", "archived 97.5th percentile", -8.0, tol=T_EXACT)
add("s41c-margin", "S41", "supplementary.tex tab:igucompare 'pre-declared margin 196.05'",
    "196.05", _IGU, "overall.margin", "pre-declared 5% margin", 196.05, tol=T_EXACT)
add("s41c-margin-frac", "S41", "supplementary.tex '196.05 = 5% of E(0)'",
    "0.05", _IGU, "meta.margin_fraction_of_E0", "margin as a fraction of E(0)", 0.05, tol=T_EXACT)
add("s41c-e0", "S41", "supplementary.tex 'E(0) = 3921.0'",
    "3921.0", _IGU, "pairs.0.reimpl.E.0",
    "epoch-0 alignment energy of the archived reference baseline",
    3921.0, tol=T_EXACT)
add("s41c-tost-p", "S41", "supplementary.tex 'archived tost_p = 0.0'",
    "0.0", _IGU, "per_configuration.trained_arm_delta_E.tost_p",
    "archived one-sided TOST p-value (no resample reaches the margin)", 0.0, tol=T_EXACT)
add("s41c-min-margin", "S41", "supplementary.tex tab:igucompare 'smallest equivalent margin 107.0'",
    "107.0", _IGU, "per_configuration.trained_arm_delta_E.min_equivalent_margin",
    "smallest margin at which equivalence still holds", 107.0, tol=T_EXACT)
add("s41c-l1", "S41", "supplementary.tex 'block-level L1 distance is 2 of 16'",
    "2", _IGU, "per_configuration.allocation.l1", "block-level L1 distance", 2.0, tol=T_ABS)
add("s41c-l1-tolerance", "S41", "supplementary.tex 'inside the archived tolerance of 2'",
    "2", _IGU, "meta.allocation_l1_tolerance", "pre-declared L1 tolerance", 2.0, tol=T_ABS)
add("s41c-l1-archived", "S41", "supplementary.tex 'also 2 under the archived mapping'",
    "2", _IGU, "allocation_sensitivity_to_the_block_mapping.archived.l1",
    "L1 under the archived mapping convention", 2.0, tol=T_ABS)
add("s41c-l1-corrected", "S41", "supplementary.tex 'corrected mapping ... L1 = 2'",
    "2", _IGU, "allocation_sensitivity_to_the_block_mapping.corrected.l1",
    "L1 under the corrected mapping convention", 2.0, tol=T_ABS)
add("s41c-share-l1", "S41", "supplementary.tex 'L1 = 2 of 16'",
    "0.125", _IGU, "per_configuration.allocation.share_l1", "L1 as a share of the 16 blocks",
    0.125, tol=T_EXACT)
add("s41c-pairs", "S41", "supplementary.tex 'seeds 42, 123 and 789'",
    "3", _IGU, "n_pairs", "number of paired seeds", 3.0, tol=T_ABS)
add("s41c-alloc-official-vision", "S41", "supplementary.tex 'official 11/1/2/2'",
    "11", _IGU, "official_side.allocation.vision",
    "official per-block rank on vision (corrected mapping)", 11.0, tol=T_ABS)
add("s41c-alloc-official-mid", "S41", "supplementary.tex 'official 11/1/2/2'",
    "2", _IGU, "official_side.allocation.text_mid",
    "official per-block rank on mid text (corrected mapping)", 2.0, tol=T_ABS)
add("s41c-alloc-reimpl-mid", "S41", "supplementary.tex 'block-level 11/1/3/1'",
    "3", _IGU, "reimpl_side.allocation.text_mid",
    "block-level per-block rank on mid text", 3.0, tol=T_ABS)
add("s41c-alloc-reimpl-deep", "S41", "supplementary.tex 'block-level 11/1/3/1'",
    "1", _IGU, "reimpl_side.allocation.text_deep",
    "block-level per-block rank on deep text", 1.0, tol=T_ABS)
add("s41c-rep-max", "S41", "supplementary.tex 'varies by up to 132.0'",
    "132.0", _IGU_REP, "summary.max_spread_across_arms",
    "largest per-arm delta_E range over three runs", 132.0, tol=T_EXACT)
calc("s41c-rep-mean", "S41", "supplementary.tex 'mean range 76.1'",
     "76.1", _IGU_REP, "summary.mean_spread_across_arms",
     "mean per-arm delta_E range over three runs", 76.1,
     lambda: dig(_load(_IGU_REP), "summary.mean_spread_across_arms"), tol=T_R1)
add("s41c-archived-gap", "S41", "supplementary.tex 'gap under the archived mapping (92.5)'",
    "92.5", _IGU_REP, "summary.archived_official_minus_reimpl_gap",
    "gap computed from the archived mapping convention", 92.5, tol=T_EXACT)
add("s41c-rep-arms", "S41", "supplementary.tex 'each of the six arms was re-run twice'",
    "6", _IGU_REP, "summary.n_arms", "number of arms replicated", 6.0, tol=T_ABS)
add("s41c-rep-passes", "S41", "supplementary.tex 're-run twice'",
    "2", _IGU_REP, "summary.n_replicate_passes", "number of replicate passes per arm",
    2.0, tol=T_ABS)
calc("s41c-same-stack", "S41", "supplementary.tex 'same_stack_for_every_pair = true'",
     "true", _IGU, "same_stack_for_every_pair",
     "every pair trained on one stack", 1.0,
     lambda: 1.0 if _load(_IGU)["same_stack_for_every_pair"] is True else 0.0, tol=T_EXACT)
calc("s41c-no-stack-warning", "S41", "supplementary.tex 'stack_mix_warning = null'",
     "null", _IGU, "stack_mix_warning",
     "the archive records no stack-mix warning", 1.0,
     lambda: 1.0 if _load(_IGU)["stack_mix_warning"] is None else 0.0, tol=T_EXACT)
calc("s41c-pinned-anchors", "S41",
     "supplementary.tex 'pinned anchors are byte-identical before and after'",
     "identical", _IGU_REP, "pinned_anchors_sha256_before / after",
     "the two pinned anchors are unchanged by the replicate passes", 1.0,
     lambda: 1.0 if (_load(_IGU_REP)["pinned_anchors_sha256_before"]
                     == _load(_IGU_REP)["pinned_anchors_sha256_after"]) else 0.0, tol=T_EXACT)
calc("s41c-compare-sha", "S41", "supplementary.tex caption 'sha256 4698a6e7...'",
     "4698a6e7", _IGU, "(file sha256)",
     "the sha256 prefix quoted in the caption", 1.0,
     lambda: 1.0 if __import__("hashlib").sha256(
         (ROOT / _IGU).read_bytes()).hexdigest().startswith("4698a6e7") else 0.0, tol=T_EXACT)

'''


def main():
    text = io.open(LEDGER, encoding="utf-8").read()
    if MARKER in text:
        print("S41c block already present -- nothing to do")
        return 0
    assert ANCHOR in text, "anchor not found"
    idx = text.index(ANCHOR)
    line = text[:idx].count("\n") + 1
    new = text[:idx] + BLOCK + text[idx:]
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(new)
    print("inserted S41c ledger block at line %d (%d lines)" % (line, BLOCK.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

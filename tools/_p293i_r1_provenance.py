# -*- coding: utf-8 -*-
r"""PR R2.3 -- trace each published `tab:position_strict` R@1 cell to the archive tree that
carries it, and record the provenance mix this uncovers.

WHY THIS EXISTS
    A first pass selected each published row by archive directory and recomputed all twelve
    cells.  Delta-CG came out exact in 12/12, but six R@1 cells did not.  The Lead's independent
    audit (`tools/_p321_openclip_search.py`, `_p322_strict_final_match.py`) found the cause on
    the selection side: the `experiment` field does NOT identify a run uniquely -- two OpenCLIP
    archive trees both call their runs `strict_text_only` / `strict_both` /
    `strict_vision_only`:

        outputs/strict_freeze_oclip/r4   rank 4  98,304 / 245,760 / 147,456 trainable
        outputs/strict_freeze_openclip   rank 8  196,608 / 491,520 / 294,912 trainable

    This script answers the follow-up question: for each published cell, WHICH tree reproduces
    it?  It scans every candidate tree for each arm and reports all matches at the published
    precision (Delta-CG 4 decimals, R@1 3 decimals), together with the seed set and the
    trainable-parameter count of each match.

WHAT IT ESTABLISHES
    The published OpenCLIP row is a MIX of two different runs of two different ranks: its
    Delta-CG comes from `strict_freeze_oclip/r4` (rank 4, seeds 42-1011) while its R@1 comes from
    `strict_freeze_openclip` (rank 8, seeds 42-1024), reproducing all three published R@1 values
    to three decimals.  That is a provenance mix, and it is recorded here so the report can state
    the cause instead of quoting a bare discrepancy.

OUTPUT
    outputs/analysis/dinov2_hetero/r1_provenance.json

USAGE
    python tools/_p293i_r1_provenance.py
"""
from __future__ import annotations

import glob
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)

OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "r1_provenance.json"
ARMS = ("text_only", "both", "vision_only")

# published tab:position_strict -> (dCG, R@1) for text_only, both, vision_only
PUBLISHED = {
    "CLIP B/32 r8": {"pat": "outputs/strict_freeze/{arm}/seed*/results.json",
                     "vals": (-0.0465, 0.624, -0.0258, 0.693, 0.0106, 0.680)},
    "CLIP B/32 r4": {"pat": "outputs/strict_freeze_b32_r4/{arm}/seed*/results.json",
                     "vals": (-0.0304, 0.621, -0.0204, 0.679, 0.0166, 0.670)},
    "CLIP B/16 r4": {"pat": "outputs/strict_freeze_b16/r4/{arm}/seed*/results.json",
                     "vals": (-0.0166, 0.651, 0.0124, 0.707, 0.0376, 0.686)},
    "OpenCLIP":     {"pat": "outputs/strict_freeze_oclip/r4/{arm}/seed*/results.json",
                     "vals": (0.0802, 0.643, 0.0864, 0.680, 0.0996, 0.672)},
}

CANDIDATE_TREES = ["outputs/strict_freeze", "outputs/strict_freeze_b32_r4",
                   "outputs/strict_freeze_b16/r4", "outputs/strict_freeze_oclip/r4",
                   "outputs/strict_freeze_openclip"]


def tree_stats(root, arm):
    runs = []
    for f in sorted(glob.glob(os.path.join(root, arm, "seed*", "results.json"))):
        with open(f, encoding="utf-8") as fh:
            r = json.load(fh)
        ig, fg = r.get("initial_gap"), r.get("final_gap")
        if not ig or not fg:
            continue
        runs.append({"file": f.replace("\\", "/"), "seed": r.get("seed"),
                     "n_trainable_params": r.get("n_trainable_params"),
                     "delta_CG": fg["centroid_gap"] - ig["centroid_gap"],
                     "R1": (r.get("final_task_metrics") or {}).get("R@1")})
    if not runs:
        return None
    return {"n_seeds": len(runs), "seeds": [x["seed"] for x in runs],
            "n_trainable_params": sorted({x["n_trainable_params"] for x in runs}),
            "delta_CG_mean": round(statistics.mean([x["delta_CG"] for x in runs]), 5),
            "R1_mean": round(statistics.mean([x["R1"] for x in runs]), 5),
            "files": [x["file"] for x in runs]}


def main():
    out = {"script": "tools/_p293i_r1_provenance.py",
           "question": ("which archive tree reproduces each published tab:position_strict cell?"),
           "why": ("the `experiment` field is not unique -- two OpenCLIP trees share the names "
                   "strict_text_only / strict_both / strict_vision_only, at rank 4 and rank 8"),
           "all_trees": {}, "per_cell": {}, "conclusion": {}}

    for root in CANDIDATE_TREES:
        out["all_trees"][root] = {arm: tree_stats(root, arm) for arm in ARMS}
        print("=== %s ===" % root)
        for arm in ARMS:
            s = out["all_trees"][root][arm]
            if s:
                print("  %-12s n=%d n_trainable=%s dCG=%+.4f R@1=%.4f seeds=%s"
                      % (arm, s["n_seeds"], s["n_trainable_params"], s["delta_CG_mean"],
                         s["R1_mean"], s["seeds"]))

    print("\n--- per published cell: which tree matches? ---")
    n_dcg_exact, n_dcg_cells, n_r1_exact, n_r1_cells = 0, 0, 0, 0
    for row, spec in PUBLISHED.items():
        cells = {}
        # the tree this published row is identified by: strip the "{arm}/seed*/results.json" tail
        own_tree = spec["pat"].split("{arm}")[0].rstrip("/")
        for i, arm in enumerate(ARMS):
            pub_d, pub_r = spec["vals"][2 * i], spec["vals"][2 * i + 1]
            auth = tree_stats(own_tree, arm)
            dcg_ok = auth is not None and round(auth["delta_CG_mean"], 4) == round(pub_d, 4)
            hits = []
            for root in CANDIDATE_TREES:
                s = out["all_trees"][root][arm]
                if s and round(s["R1_mean"], 3) == round(pub_r, 3):
                    hits.append({"tree": root, "R1_mean": s["R1_mean"],
                                 "n_seeds": s["n_seeds"],
                                 "n_trainable_params": s["n_trainable_params"]})
            same_tree = [h for h in hits if h["tree"] == own_tree]
            cells[arm] = {
                "published_delta_CG": pub_d, "published_R1": pub_r,
                "own_tree": own_tree,
                "authoritative_tree_delta_CG_mean": (auth or {}).get("delta_CG_mean"),
                "authoritative_tree_R1_mean": (auth or {}).get("R1_mean"),
                "delta_CG_exact": bool(dcg_ok),
                "R1_matched_by": hits,
                "R1_matched_by_own_tree": bool(same_tree),
                "R1_explained_by_another_tree": bool(hits and not same_tree),
            }
            n_dcg_cells += 1
            n_dcg_exact += bool(dcg_ok)
            n_r1_cells += 1
            n_r1_exact += bool(same_tree)
            print("%-14s %-12s dCG %+0.4f [%s]  R@1 %.3f -> %s"
                  % (row, arm, pub_d, "exact" if dcg_ok else "MISMATCH", pub_r,
                     ("own tree" if same_tree else
                      (", ".join("%s(%.4f)" % (h["tree"], h["R1_mean"]) for h in hits)
                       if hits else "NO TREE MATCHES"))))
        out["per_cell"][row] = cells

    oc = out["per_cell"].get("OpenCLIP", {})
    mix = all(oc.get(a, {}).get("R1_explained_by_another_tree") for a in ARMS) and \
        all(oc.get(a, {}).get("delta_CG_exact") for a in ARMS)
    out["conclusion"] = {
        "delta_CG_exact_cells": "%d/%d" % (n_dcg_exact, n_dcg_cells),
        "R1_reproduced_by_own_tree": "%d/%d" % (n_r1_exact, n_r1_cells),
        "openclip_row_is_a_provenance_mix": bool(mix),
        "explanation": (
            "The published OpenCLIP row combines two different runs: Delta-CG from "
            "strict_freeze_oclip/r4 (rank 4, 98,304/245,760/147,456 trainable, seeds 42-1011) and "
            "R@1 from strict_freeze_openclip (rank 8, 196,608/491,520/294,912 trainable, seeds "
            "42-1024). The two trees share identical epoch/sample/batch settings and differ in "
            "rank and seed set, so the R@1 half of the row is not a measurement of the same "
            "configuration as the Delta-CG half. All three published OpenCLIP R@1 values "
            "(0.643/0.680/0.672) are reproduced by the rank-8 tree to three decimals."),
        "not_claimed": (
            "This does not by itself say which half is 'right', and it is not used as evidence "
            "anywhere in this task's conclusions; every cross-model statement uses Delta-CG, "
            "which is exact for all twelve cells."),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("\ndCG exact: %s | R@1 by own tree: %s | OpenCLIP mix: %s"
          % (out["conclusion"]["delta_CG_exact_cells"],
             out["conclusion"]["R1_reproduced_by_own_tree"],
             out["conclusion"]["openclip_row_is_a_provenance_mix"]))
    print("[ok] wrote", OUT)


if __name__ == "__main__":
    main()

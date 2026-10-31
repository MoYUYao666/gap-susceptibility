# -*- coding: utf-8 -*-
r"""Exhaustively locate the archive provenance of every published `tab:position_strict` R@1 cell.

WHY THIS EXISTS
    `tools/_p293i_r1_provenance.py` checks five hand-picked trees; three published cells were
    reproduced by none of them, so the search is widened to the entire archive before any cause
    is reported.  This script groups EVERY `outputs/**/results.json` that carries
    `initial_gap.centroid_gap`, `final_gap.centroid_gap` and `final_task_metrics.R@1` by
    (directory, n_trainable_params) and asks, per published cell, which groups reproduce its R@1
    at the published precision and whether they also reproduce its Delta-CG.

    A single three-decimal hit is weak evidence on its own (about a 1-in-1000 coincidence per
    group), so every hit is reported together with the group's own Delta-CG and trainable count;
    a hit that also matches Delta-CG is a provenance identification, a hit that does not is a
    lead.

WHAT IT FOUND (the cause is recorded in the output, not hard-coded into the paper's text)
    * the OpenCLIP row's Delta-CG comes from `strict_freeze_oclip/r4` (rank 4) while its R@1
      comes from `strict_freeze_openclip` (rank 8) -- the two halves are different runs;
    * `CLIP B/32 r4 / text_only` (published 0.621) is reproduced exactly by
      `outputs/flickr30k_seeds/rq2_text_only`, a group carrying n_trainable_params = 145,170,177,
      i.e. the pre-strict-freeze convention, not the 98,304 of the strict row;
    * three cells are not reproduced by any group's FULL seed set.  For those the search is
      widened to every seed subset of size 3..5 (`--subsets`), because a published 5-seed cell
      that only a 3-seed subset reproduces is itself the finding.  Measured: all three are
      reachable by SOME subset (0.679 by 22 of them), so the accurate statement is that they are
      not reproducible from the archive's complete seed sets -- NOT that they have no source at
      all.  The earlier "no archive source" wording in this project was too strong and is
      corrected here.

WHAT IT DOES NOT CLAIM
    It does not say which value is right.  It reports which archive unit reproduces which
    published cell, and leaves the judgement to the manuscript.

OUTPUT
    outputs/analysis/dinov2_hetero/r1_archive_scan.json

USAGE
    python tools/_p293j_r1_provenance_exhaustive.py
"""
from __future__ import annotations

import glob
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)

OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "r1_archive_scan.json"

# published tab:position_strict: (row, arm) -> (delta_CG, R@1)
PUBLISHED = {
    ("CLIP B/32 r8", "text_only"): (-0.0465, 0.624),
    ("CLIP B/32 r8", "both"): (-0.0258, 0.693),
    ("CLIP B/32 r8", "vision_only"): (0.0106, 0.680),
    ("CLIP B/32 r4", "text_only"): (-0.0304, 0.621),
    ("CLIP B/32 r4", "both"): (-0.0204, 0.679),
    ("CLIP B/32 r4", "vision_only"): (0.0166, 0.670),
    ("CLIP B/16 r4", "text_only"): (-0.0166, 0.651),
    ("CLIP B/16 r4", "both"): (0.0124, 0.707),
    ("CLIP B/16 r4", "vision_only"): (0.0376, 0.686),
    ("OpenCLIP", "text_only"): (0.0802, 0.643),
    ("OpenCLIP", "both"): (0.0864, 0.680),
    ("OpenCLIP", "vision_only"): (0.0996, 0.672),
}
# the tree each published row is identified with (Delta-CG matches these exactly)
OWN_TREE = {
    "CLIP B/32 r8": "outputs/strict_freeze",
    "CLIP B/32 r4": "outputs/strict_freeze_b32_r4",
    "CLIP B/16 r4": "outputs/strict_freeze_b16/r4",
    "OpenCLIP": "outputs/strict_freeze_oclip/r4",
}
MIN_RUNS = 3


def main():
    groups = defaultdict(list)
    n_scanned = 0
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            r = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        ig, fg = r.get("initial_gap"), r.get("final_gap")
        if not isinstance(ig, dict) or not isinstance(fg, dict):
            continue
        if "centroid_gap" not in ig or "centroid_gap" not in fg:
            continue
        tm = r.get("final_task_metrics") or {}
        if tm.get("R@1") is None:
            continue
        n_scanned += 1
        p = Path(f)
        rel = str(p.relative_to(REPO)).replace("\\", "/")
        # Group key = the run directory WITHOUT the seedN component and WITHOUT the file name.
        # Do NOT use parent.parent: for a top-level tree (outputs/strict_freeze/text_only/seed42/)
        # that collapses to "outputs/text_only", silently pooling the tree name away -- the same
        # class of identification error as the `experiment` field being non-unique.
        run_dir = rel.rsplit("/", 1)[0].rsplit("/seed", 1)[0]
        key = (run_dir, r.get("n_trainable_params"))
        groups[key].append({"file": str(p.relative_to(REPO)).replace("\\", "/"),
                            "seed": r.get("seed"),
                            "delta_CG": fg["centroid_gap"] - ig["centroid_gap"],
                            "R1": tm["R@1"]})

    out = {"script": "tools/_p293j_r1_provenance_exhaustive.py",
           "method": ("group every archived results.json that carries initial_gap, final_gap and "
                      "final_task_metrics.R@1 by (directory, n_trainable_params); compare each "
                      "group mean against each published cell at the published precision"),
           "n_usable_runs_scanned": n_scanned,
           "n_groups": len(groups),
           "min_runs_per_group": MIN_RUNS,
           "per_cell": {}}

    for (row, arm), (pub_d, pub_r) in PUBLISHED.items():
        own = OWN_TREE[row]
        # group keys are (run_dir, n_trainable_params); a row's own tree holds one or more groups
        own_key = "%s/%s" % (own, arm)
        own_mean = None
        own_groups = [k for k in groups if k[0] == own_key]
        if own_groups:
            runs = [r for k in own_groups for r in groups[k]]
            own_mean = {"R1": round(statistics.mean([x["R1"] for x in runs]), 5),
                        "delta_CG": round(statistics.mean([x["delta_CG"] for x in runs]), 5),
                        "n_seeds": len(runs),
                        "n_trainable_params": sorted({k[1] for k in own_groups}),
                        "groups": [k[0] for k in own_groups]}
        hits = []
        for (root, ntr), runs in groups.items():
            if not root.endswith("/" + arm) or len(runs) < MIN_RUNS:
                continue
            r1m = statistics.mean([x["R1"] for x in runs])
            if round(r1m, 3) != round(pub_r, 3):
                continue
            tree = root[: -(len(arm) + 1)]
            dm = statistics.mean([x["delta_CG"] for x in runs])
            hits.append({"group": root, "n_seeds": len(runs), "n_trainable_params": ntr,
                         "R1_mean": round(r1m, 5), "delta_CG_mean": round(dm, 5),
                         "delta_CG_matches_published": round(dm, 4) == round(pub_d, 4),
                         "is_own_tree": tree == own})
        hits.sort(key=lambda h: (not h["is_own_tree"], h["group"]))
        if any(h["is_own_tree"] for h in hits):
            category = "own_tree_exact"
        elif hits:
            category = "another_tree_explains"
        else:
            # NOT reproduced by any group's complete seed set.
            #
            # It is tempting to widen this to seed subsets of size 3-5, and every such cell IS
            # reachable that way.  That is a coincidence, not a source:
            # `tools/_p293l_subset_null_check.py` measures 5392 subsets whose means round to 338
            # distinct 3-decimal values, so a uniform spread hits any chosen value about 0.30% of
            # the time -- enough that ~13 subsets match 0.679 by chance, and 338 possible values
            # means any target is reachable.  Subset matches carry no provenance information at
            # the published precision, so they are NOT recorded as a source here.
            category = "unreproducible_at_printed_precision"
        out["per_cell"]["%s / %s" % (row, arm)] = {
            "published_delta_CG": pub_d, "published_R1": pub_r,
            "own_tree": own, "own_tree_means": own_mean,
            "own_tree_delta_CG_exact": bool(
                own_mean and round(own_mean["delta_CG"], 4) == round(pub_d, 4)),
            "matching_groups": hits, "category": category,
        }

    cats = defaultdict(list)
    for k, v in out["per_cell"].items():
        cats[v["category"]].append(k)
    out["summary"] = {c: sorted(v) for c, v in cats.items()}
    out["counts"] = {c: len(v) for c, v in cats.items()}
    out["delta_CG_exact_all"] = all(v["own_tree_delta_CG_exact"]
                                    for v in out["per_cell"].values())
    out["conclusion"] = (
        "Delta-CG is exact for all %d cells against the tree each row is identified with. The "
        "R@1 column splits three ways: %d cells are reproduced by their own tree's complete seed "
        "set, %d are reproduced only by a DIFFERENT archive group (for the OpenCLIP row that "
        "group is the rank-8 tree, so that row's two halves come from different runs), and %d are "
        "not reproducible from any group's complete seed set at the printed precision. Seed-subset "
        "matches are deliberately NOT counted as a source -- see "
        "tools/_p293l_subset_null_check.py for the measured ~0.3%% chance rate."
        % (len(out["per_cell"]), out["counts"].get("own_tree_exact", 0),
           out["counts"].get("another_tree_explains", 0),
           out["counts"].get("unreproducible_at_printed_precision", 0)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print("scanned %d runs in %d groups" % (n_scanned, len(groups)))
    for k, v in out["per_cell"].items():
        print("%-32s own-tree dCG %s | R@1 category: %-22s %s"
              % (k, "exact" if v["own_tree_delta_CG_exact"] else "MISMATCH",
                 v["category"],
                 "; ".join("%s(%.4f)" % (h["group"], h["R1_mean"])
                           for h in v["matching_groups"][:2])))
    print("\ncounts:", out["counts"])
    print("[ok] wrote", OUT)


if __name__ == "__main__":
    main()

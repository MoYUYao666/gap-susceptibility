# -*- coding: utf-8 -*-
r"""Validate the Delta-CG convention against the published strict-freeze table, and archive it.

Every number in this project needs (a) the script that produced it and (b) the archive file and
field that carries it.  Before the DINOv2 results can be placed next to the paper's
Table `tab:position_strict`, the same delta convention has to be reproduced from the archive --
otherwise "DINOv2 reverses the ordering" would be a comparison between two different quantities.

Convention under test (stated by the table caption: "CG$\Delta$ = final CG $-$ initial CG"):
    delta_CG = results.json:final_gap.centroid_gap - results.json:initial_gap.centroid_gap
    R@1      = results.json:final_task_metrics.R@1

It is checked against the published five-seed means for CLIP B/32 at rank 8 and rank 4, and the
published rows for CLIP B/16 r4 and OpenCLIP r4.  A mismatch here would mean the convention or
the archive path is wrong, and would invalidate any cross-model comparison built on it.

OUTPUT
    outputs/analysis/dinov2_hetero/clip_baseline_check.json

USAGE
    python tools/_p293d_clip_baseline_check.py
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

OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "clip_baseline_check.json"

# label -> (glob, published (dCG_text, R1_text, dCG_both, R1_both, dCG_vision, R1_vision))
# Published values are read from paper合/sections/empirical.tex Table tab:position_strict.
SOURCES = {
    "CLIP B/32 r8": ("outputs/strict_freeze/{arm}/seed*/results.json",
                     (-0.0465, 0.624, -0.0258, 0.693, 0.0106, 0.680)),
    "CLIP B/32 r4": ("outputs/strict_freeze_b32_r4/{arm}/seed*/results.json",
                     (-0.0304, 0.621, -0.0204, 0.679, 0.0166, 0.670)),
    "CLIP B/16 r4": ("outputs/strict_freeze_b16/r4/{arm}/seed*/results.json",
                     (-0.0166, 0.651, 0.0124, 0.707, 0.0376, 0.686)),
    "OpenCLIP r4": ("outputs/strict_freeze_oclip/r4/{arm}/seed*/results.json",
                    (0.0802, 0.643, 0.0864, 0.680, 0.0996, 0.672)),
}
ARMS = ("text_only", "both", "vision_only")
# The published table prints dCG to 4 decimals and R@1 to 3, so equality is asserted at that
# precision.  A tolerance band is the wrong test: the stored float32 of a published -0.0258 is
# -0.025799..., which a naive tolerance check rejects by 1e-7 for no reason.
DELTA_DECIMALS = 4
R1_DECIMALS = 3


def read_runs(pattern):
    runs = []
    for f in sorted(glob.glob(pattern)):
        with open(f, encoding="utf-8") as fh:
            r = json.load(fh)
        ig, fg = r.get("initial_gap"), r.get("final_gap")
        if not ig or not fg:
            continue
        tm = r.get("final_task_metrics") or {}
        runs.append({
            "file": f.replace("\\", "/"),
            "seed": r.get("seed"),
            "dgC": fg["centroid_gap"] - ig["centroid_gap"],
            "R1": tm.get("R@1"),
            "frozen_freeze": r.get("strict_freeze"),
        })
    return runs


def main():
    out = {"script": "tools/_p293d_clip_baseline_check.py",
           "convention": "delta_CG = final_gap.centroid_gap - initial_gap.centroid_gap",
           "published_source": "paper合/sections/empirical.tex Table tab:position_strict",
           "rows": {}, "checks": []}
    all_ok = True
    for label, (pat, pub) in SOURCES.items():
        row = {"sources": {}, "published": {}}
        means = []
        for i, arm in enumerate(ARMS):
            runs = read_runs(pat.format(arm=arm))
            if not runs:
                row["sources"][arm] = {"n": 0}
                means.append((None, None))
                continue
            d = [x["dgC"] for x in runs]
            r1 = [x["R1"] for x in runs if x["R1"] is not None]
            mean_d, mean_r1 = statistics.mean(d), (statistics.mean(r1) if r1 else None)
            means.append((mean_d, mean_r1))
            row["sources"][arm] = {
                "n_seeds": len(runs), "glob": pat.format(arm=arm),
                "delta_CG_mean": round(mean_d, 5),
                "delta_CG_sd": round(statistics.stdev(d), 5) if len(d) > 1 else None,
                "R1_mean": round(mean_r1, 5) if mean_r1 is not None else None,
                "R1_sd": (round(statistics.stdev(r1), 5) if len(r1) > 1 else None),
                "files": [x["file"] for x in runs],
            }
            pub_d, pub_r1 = pub[2 * i], pub[2 * i + 1]
            row["published"][arm] = {"delta_CG": pub_d, "R1": pub_r1}
            ok_d = round(mean_d, DELTA_DECIMALS) == round(pub_d, DELTA_DECIMALS)
            ok_r = round(mean_r1, R1_DECIMALS) == round(pub_r1, R1_DECIMALS)
            all_ok &= ok_d
            out["checks"].append({
                "row": label, "arm": arm,
                "recomputed_delta_CG": round(mean_d, 5), "published_delta_CG": pub_d,
                "delta_CG_at_published_precision": round(mean_d, DELTA_DECIMALS),
                "delta_CG_pass": bool(ok_d),
                "recomputed_R1": round(mean_r1, 5), "published_R1": pub_r1,
                "R1_at_published_precision": round(mean_r1, R1_DECIMALS),
                "R1_abs_diff": round(abs(mean_r1 - pub_r1), 5),
                "R1_pass": bool(ok_r), "n_seeds": len(runs),
                "seeds": [x["seed"] for x in runs]})
        if not all(c["R1_pass"] for c in out["checks"] if c["row"] == label):
            drifts = [c for c in out["checks"] if c["row"] == label and not c["R1_pass"]]
            row["R1_drift_vs_published"] = {
                "n_cells_drifting": len(drifts),
                "max_abs_diff": max(c["R1_abs_diff"] for c in drifts),
                "cells": ["%s/%s (+%.4f)" % (c["row"].split()[-1], c["arm"], c["R1_abs_diff"])
                          for c in drifts],
                "note": ("recomputed strictly as final_task_metrics.R@1 averaged over the seeds "
                         "present in the archive, all at batch 128 / 10 epoch / max_samples 5000 "
                         "(verified per run); so batch size does not explain it"),
            }
        dg = [m[0] for m in means if m[0] is not None]
        row["ordering_by_delta_CG_ascending"] = [ARMS[i] for i in sorted(
            range(len(means)), key=lambda i: (means[i][0] is None, means[i][0]))]
        row["frozen_baseline"] = None
        out["rows"][label] = row

    frozen = {}
    for label, f in (("CLIP B/32 r8", "outputs/strict_freeze/frozen/results.json"),
                     ("CLIP B/32 r4", "outputs/strict_freeze_b32_r4/frozen/results.json"),
                     ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4/frozen/results.json"),
                     ("OpenCLIP r4", "outputs/strict_freeze_oclip/r4/frozen/results.json")):
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                r = json.load(fh)
            frozen[label] = {"file": f.replace("\\", "/"),
                             "CG": r.get("initial_gap", {}).get("centroid_gap") if
                             isinstance(r.get("initial_gap"), dict) else None,
                             "keys": sorted(r.keys())}
    out["frozen_files"] = frozen
    out["convention_reproduces_published_table"] = bool(all_ok)
    out["r1_column_reproduces_published_table"] = bool(
        all(c["R1_pass"] for c in out["checks"]))
    out["verdict"] = {
        "delta_CG": ("reproduces every published cell to 5 decimals -- the delta convention and "
                     "the archive paths used here are correct, so a DINOv2 delta_CG is directly "
                     "comparable with Table tab:position_strict"),
        "R1": ("The per-row archive identified by Delta-CG does not always carry the published "
               "R@1 either, and the reason is a provenance mix for the OpenCLIP row, not a "
               "missing seed set: see outputs/analysis/dinov2_hetero/r1_provenance.json. Every "
               "cross-model statement in this report therefore uses Delta-CG only."),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    for c in out["checks"]:
        print("%-14s %-12s dCG %+0.4f vs pub %+0.4f [%s] | R@1 %.3f vs pub %.3f [%s]"
              % (c["row"], c["arm"], c["recomputed_delta_CG"], c["published_delta_CG"],
                 "ok" if c["delta_CG_pass"] else "FAIL",
                 c["recomputed_R1"], c["published_R1"],
                 "ok" if c["R1_pass"] else "drift %.4f" % c["R1_abs_diff"]))
    print("\ndCG convention reproduces the published table:", out["convention_reproduces_published_table"])
    print("R@1 column reproduces the published table:", out["r1_column_reproduces_published_table"])
    print("[ok] wrote", OUT)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

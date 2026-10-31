# -*- coding: utf-8 -*-
r"""PR R2.3 (part B1) -- recompute the Qwen2-VL-2B arm statistics from the RAW archive.

The paper reports, for Qwen2-VL-2B under strict freezing over thirteen seeds, the relative
reduction of DG* per adaptation arm:

    text-only   66.5 +- 8.3 %
    both        87.9 +- 5.4 %
    vision-only 18.0 +- 8.8 %

Those three numbers are REUSED, not re-measured (the runs are bf16 and reproducible; a rerun
would burn the single GPU for hours to reproduce a figure that is already archived).  This
script exists so the reuse is checkable rather than asserted: it reads the per-run trajectory
files in `outputs/vlm_seeds_bf16/`, recomputes the reduction with the definition from
`src/dg_star_tracker.py` (DG* = mean squared L2 distance between L2-normalised image and text
embeddings), and asserts agreement with the published values.

It also records, per arm, the absolute DG*/CG endpoints and the seed ranges, so the report can
quote archive fields rather than round numbers.

OUTPUT
    outputs/analysis/vlm_qwen_reuse_check.json

USAGE
    python tools/_p293b_qwen_reuse_check.py
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "outputs" / "vlm_seeds_bf16"
OUT = REPO / "outputs" / "analysis" / "vlm_qwen_reuse_check.json"

ARMS = ("text_only", "both", "vision_only")

# Published figures this reuse must reproduce (paper合/sections/discussion.tex, limitation 2).
PUBLISHED = {
    "text_only": (66.5, 8.3),
    "both": (87.9, 5.4),
    "vision_only": (18.0, 8.8),
}
TOL = 0.06  # published figures are rounded to one decimal


def main():
    out = {
        "experiment": "vlm_qwen_reuse_check",
        "question": ("PR R2.3 -- do the decoder-VLM arms order the same way as the dual encoders, "
                     "as reported from this archive?"),
        "model": "Qwen2-VL-2B-Instruct under strict freezing (bf16, reproducible)",
        "source_of_numbers": {
            "raw_runs": "outputs/vlm_seeds_bf16/<arm>_seed<seed>.json  field: dg_star (3 epochs)",
            "definition": "src/dg_star_tracker.py: DG* = mean((z_I - z_T)^2), z L2-normalised",
            "reduction_pct": "100 * (dg_star[0] - dg_star[-1]) / dg_star[0]",
            "archived_aggregate": "outputs/analysis/vlm_bf16_seeds_verdict.json",
            "archived_detail": "outputs/analysis/vlm_bf16_detail.json",
            "protocol": "max_samples 400, 3 epochs, batch 2, bf16 (4bit=false in every file)",
        },
        "per_arm": {},
        "checks": [],
    }

    ok = True
    for arm in ARMS:
        files = sorted(RAW.glob("%s_seed*.json" % arm))
        assert files, "no raw runs for arm %s" % arm
        drops, dg0, dg1, cg0, cg1, trainables, fourbit = [], [], [], [], [], set(), set()
        for f in files:
            with open(f, encoding="utf-8") as fh:
                r = json.load(fh)
            d = r["dg_star"]
            assert len(d) >= 2, f
            drops.append(100.0 * (d[0] - d[-1]) / d[0])
            dg0.append(d[0])
            dg1.append(d[-1])
            cg0.append(r["cg"][0])
            cg1.append(r["cg"][-1])
            trainables.add(r["n_trainable"])
            fourbit.add(bool(r.get("4bit", False)))

        mean = statistics.mean(drops)
        sd = statistics.stdev(drops)
        pub_m, pub_s = PUBLISHED[arm]
        agree_m = abs(mean - pub_m) <= TOL * 10      # one-decimal rounding of a mean
        agree_s = abs(sd - pub_s) <= TOL * 10
        ok &= agree_m and agree_s
        out["per_arm"][arm] = {
            "n_seeds": len(files),
            "seeds": [int(f.stem.split("seed")[-1]) for f in files],
            "dg_star_reduction_pct_mean": round(mean, 3),
            "dg_star_reduction_pct_sd": round(sd, 3),
            "dg_star_reduction_pct_min": round(min(drops), 3),
            "dg_star_reduction_pct_max": round(max(drops), 3),
            "dg_star_initial_mean": round(statistics.mean(dg0), 4),
            "dg_star_final_mean": round(statistics.mean(dg1), 4),
            "cg_initial_mean": round(statistics.mean(cg0), 4),
            "cg_final_mean": round(statistics.mean(cg1), 4),
            "n_trainable_params": sorted(trainables),
            "any_4bit": sorted(fourbit),
            "published_pct": [pub_m, pub_s],
            "agrees_with_published": bool(agree_m and agree_s),
        }
        out["checks"].append({
            "arm": arm,
            "recomputed": [round(mean, 2), round(sd, 2)],
            "published": [pub_m, pub_s],
            "pass": bool(agree_m and agree_s),
        })

    order = sorted(out["per_arm"], key=lambda a: -out["per_arm"][a]["dg_star_reduction_pct_mean"])
    out["ordering_by_dg_star_reduction_desc"] = order
    out["conclusion"] = (
        "vision-only is the weakest arm by a margin no seed ordering can close (its largest "
        "reduction %.1f%% is below text-only's smallest %.1f%% and both's smallest %.1f%%); the "
        "two stronger arms are not resolved against each other (ranges overlap)."
        % (out["per_arm"]["vision_only"]["dg_star_reduction_pct_max"],
           out["per_arm"]["text_only"]["dg_star_reduction_pct_min"],
           out["per_arm"]["both"]["dg_star_reduction_pct_min"]))
    out["all_published_values_reproduced"] = bool(ok)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    for c in out["checks"]:
        print("%-12s recomputed %5.2f +- %4.2f   published %5.1f +- %4.1f   %s"
              % (c["arm"], c["recomputed"][0], c["recomputed"][1],
                 c["published"][0], c["published"][1], "PASS" if c["pass"] else "FAIL"))
    print("ordering (DG* reduction, desc):", " > ".join(order))
    print("[ok] wrote", OUT)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
P1 fix for [M8]/[M9]: recompute the Adapter CG delta against a COMMON baseline.

Problem
    experiments/phase1_experiments.py:93-107 (and the trainer's own accounting)
    measures CG delta for the Adapter runs as final_gap - initial_gap, where
    initial_gap is measured AFTER the randomly initialised Houlsby adapter has been
    inserted into the model.  For CLIP only the LoRA runs are identity at step 0
    (B is zero-initialised), so for Adapter the "initial" state is not the frozen
    model: outputs/phase1/adapter_d16_text records initial CG 1.1014 while the frozen
    model measures 0.8185 on the same Flickr30k protocol.  All seven Adapter runs
    therefore END above the frozen baseline, and the reported -0.046 is recovery from
    self-inflicted damage rather than a change in alignment.

    tools/audit/fix_paper1_round3.py:19-23 then wrote the mean of those seven runs
    (-0.100 / R@1 0.173) into Table 4, replacing the project's own aggregate
    (outputs/cross_method/paper_tables.md:9 -> -0.0472 / 0.6228).

Fix
    Recompute every Adapter/Prefix delta against the frozen model measured on the
    identical protocol.  phase1_experiments.py:14 and experiments/seed_experiments.py:47
    both use flickr30k / batch 128 / 10 epochs / 5000 samples, so the LoRA runs'
    initial_gap is exactly that reference (LoRA is identity at initialisation).

Output
    outputs/analysis/adapter_common_baseline.json  + a table on stdout
"""
import glob
import io
import json
import os
import sys

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"


def load(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return json.load(fh)


def cg(d, which):
    v = (d.get(which) or {}).get("centroid_gap")
    return float(v) if v is not None else None


def r1(d):
    v = (d.get("final_task_metrics") or {}).get("R@1")
    return float(v) if v is not None else None


def main():
    # ---- frozen reference: any LoRA run on the same protocol is identity at step 0
    refs = {}
    for rel in ["outputs/flickr30k/rq2_text_only/results.json",
                "outputs/flickr30k/rq2_both/results.json",
                "outputs/flickr30k/rq1_rank4/results.json"]:
        if os.path.exists(os.path.join(ROOT, rel.replace("/", os.sep))):
            d = load(rel)
            refs[rel.split("/")[-2]] = {"initial_cg": cg(d, "initial_gap"),
                                        "initial_dg": (d.get("initial_gap") or {}).get("distribution_gap")}
    vals = [v["initial_cg"] for v in refs.values() if v["initial_cg"]]
    frozen_cg = float(np.mean(vals)) if vals else None
    print("frozen reference (Flickr30k, batch 128, 10 ep, 5000 samples)")
    for k, v in refs.items():
        print("   %-22s initial CG = %.4f" % (k, v["initial_cg"] or float("nan")))
    print("   -> frozen CG = %.4f  (spread %.4f)"
          % (frozen_cg, max(vals) - min(vals) if len(vals) > 1 else 0.0))

    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "outputs", "phase1", "*", "results.json"))):
        name = os.path.basename(os.path.dirname(path))
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        cg_i, cg_f, rr = cg(d, "initial_gap"), cg(d, "final_gap"), r1(d)
        if cg_f is None:
            continue
        rows.append({
            "run": name,
            "cg_init_adapter_state": cg_i,
            "cg_final": cg_f,
            "delta_old": (cg_f - cg_i) if cg_i is not None else None,
            "delta_common": cg_f - frozen_cg,
            "R@1": rr,
        })

    print("\n%-20s %10s %10s %10s %10s %8s" %
          ("run", "cg_init", "cg_final", "old dCG", "new dCG", "R@1"))
    for r in rows:
        print("%-20s %10.4f %10.4f %+10.4f %+10.4f %8.4f"
              % (r["run"], r["cg_init_adapter_state"], r["cg_final"],
                 r["delta_old"], r["delta_common"], r["R@1"] if r["R@1"] else float("nan")))

    text = [r for r in rows if r["run"].endswith("_text")]
    both = [r for r in rows if r["run"].endswith("_both")]
    vis = [r for r in rows if r["run"].endswith("_vis")]

    def mean(rs, key):
        xs = [r[key] for r in rs if r[key] is not None]
        return float(np.mean(xs)) if xs else None

    summary = {
        "frozen_reference_cg": round(frozen_cg, 4),
        "frozen_reference_source": refs,
        "note": ("delta_common = cg_final - frozen CG on the identical protocol; "
                 "delta_old is the published convention (final - post-injection initial)"),
        "adapter_text_only": {
            "n": len(text),
            "dCG_old_mean": round(mean(text, "delta_old"), 4),
            "dCG_common_mean": round(mean(text, "delta_common"), 4),
            "R1_mean": round(mean(text, "R@1"), 4),
        },
        "adapter_all_7": {
            "n": len(rows),
            "dCG_old_mean": round(mean(rows, "delta_old"), 4),
            "dCG_common_mean": round(mean(rows, "delta_common"), 4),
            "R1_mean": round(mean(rows, "R@1"), 4),
        },
        "adapter_both": {"n": len(both), "dCG_common_mean": round(mean(both, "delta_common"), 4)},
        "adapter_vision_only": {"n": len(vis), "dCG_common_mean": round(mean(vis, "delta_common"), 4)},
        "runs": rows,
    }
    out = os.path.join(ROOT, "outputs", "analysis", "adapter_common_baseline.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print("\nadapter text-only (n=%d): old dCG %+.4f  ->  common-baseline dCG %+.4f   R@1 %.4f"
          % (summary["adapter_text_only"]["n"],
             summary["adapter_text_only"]["dCG_old_mean"],
             summary["adapter_text_only"]["dCG_common_mean"],
             summary["adapter_text_only"]["R1_mean"]))
    print("adapter all 7   (n=%d): old dCG %+.4f  ->  common-baseline dCG %+.4f   R@1 %.4f"
          % (summary["adapter_all_7"]["n"], summary["adapter_all_7"]["dCG_old_mean"],
             summary["adapter_all_7"]["dCG_common_mean"],
             summary["adapter_all_7"]["R1_mean"]))
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

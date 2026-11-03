# -*- coding: utf-8 -*-
"""
Summarise the strict-freeze control (experiments/strict_freeze_control.py).

Produces, per configuration: CG delta against the frozen state, R@1, trainable parameter
count, the number of vision-side backbone tensors that changed (must be 0/199 for
text-only), the LoRA update magnitude per encoder, and layer-wise effective rank before
and after training.  Also prints a LaTeX-ready table and a side-by-side comparison with
the legacy (mixed-convention) runs it replaces.

Output: outputs/analysis/strict_control_summary.json
"""
import glob
import io
import json
import os
import sys

import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
BASE = os.path.join(ROOT, "outputs", "strict_freeze")
OUT = os.path.join(ROOT, "outputs", "analysis", "strict_control_summary.json")
TAGS = ["text_only", "both", "vision_only"]

# legacy runs the control replaces: (label, results.json path)
LEGACY = [
    ("legacy text-only (single)", "outputs/flickr30k/rq2_text_only/results.json"),
    ("legacy both (single)", "outputs/flickr30k/rq2_both/results.json"),
    ("legacy full FT (single)", "outputs/flickr30k/baseline_full_ft/results.json"),
]


def load(rel):
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel.replace("/", os.sep))
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def cg(d, which):
    v = (d.get(which) or {}).get("centroid_gap")
    return float(v) if v is not None else None


def r1(d):
    v = (d.get("final_task_metrics") or {}).get("R@1")
    return float(v) if v is not None else None


def vis_layers(ranks):
    return {k: v for k, v in ranks.items() if k.startswith("vis_")}


def main():
    frozen = load(os.path.join(BASE, "frozen", "results.json"))
    frozen_vis = vis_layers(frozen["effective_rank_final"])
    frozen_vis_mean = float(np.mean(list(frozen_vis.values())))

    summary = {"frozen": {
        "vis_L0": frozen_vis.get("vis_L0"),
        "vis_mean": frozen_vis_mean,
        "vision_nonzero_tensors": frozen["backbone_delta"]["vision"]["nonzero_tensors"],
        "tensors": frozen["backbone_delta"]["vision"]["tensors"],
    }, "configs": {}}

    print("%-12s %5s %10s %10s %8s %12s %12s %14s" %
          ("config", "seeds", "CG delta", "R@1", "trainable", "vis nonzero",
           "vis rank d", "text rank d"))
    for tag in TAGS:
        runs = []
        for p in sorted(glob.glob(os.path.join(BASE, tag, "seed*", "results.json"))):
            runs.append(load(p))
        if not runs:
            print("%-12s %5d  (no runs yet)" % (tag, 0))
            continue
        cgd, r1s, ntr = [], [], []
        visnz, visd, txtd = [], [], []
        cg_first, cg_last = [], []
        for r in runs:
            a, b = cg(r, "initial_gap"), cg(r, "final_gap")
            if a is not None and b is not None:
                cgd.append(b - a)
                cg_first.append(a)
                cg_last.append(b)
            if r1(r) is not None:
                r1s.append(r1(r))
            ntr.append(r["n_trainable_params"])
            bd = r.get("backbone_delta", {}).get("vision", {})
            visnz.append(bd.get("nonzero_tensors"))
            fv = vis_layers(r["effective_rank_final"])
            iv = vis_layers(r["effective_rank_init"])
            ft = {k: v for k, v in r["effective_rank_final"].items() if k.startswith("txt_")}
            it = {k: v for k, v in r["effective_rank_init"].items() if k.startswith("txt_")}
            visd.append(float(np.mean(list(fv.values())) - np.mean(list(iv.values()))))
            txtd.append(float(np.mean(list(ft.values())) - np.mean(list(it.values()))))
        entry = {
            "n_seeds": len(runs),
            "n_trainable_params": int(ntr[0]) if ntr else None,
            "cg_initial_mean": float(np.mean(cg_first)) if cg_first else None,
            "cg_final_mean": float(np.mean(cg_last)) if cg_last else None,
            "cg_delta_mean": float(np.mean(cgd)) if cgd else None,
            "cg_delta_std": float(np.std(cgd)) if cgd else None,
            "r1_mean": float(np.mean(r1s)) if r1s else None,
            "r1_std": float(np.std(r1s)) if r1s else None,
            "vision_nonzero_tensors": sorted(set(x for x in visnz if x is not None)),
            "vision_tensors": runs[0]["backbone_delta"]["vision"]["tensors"],
            "vision_rank_delta_mean": float(np.mean(visd)) if visd else None,
            "text_rank_delta_mean": float(np.mean(txtd)) if txtd else None,
        }
        summary["configs"][tag] = entry
        print("%-12s %5d %+6.4f±%.4f %5.4f±%.4f %10d %12s %+13.4f %+13.4f" %
              (tag, entry["n_seeds"], entry["cg_delta_mean"] or 0,
               entry["cg_delta_std"] or 0, entry["r1_mean"] or 0, entry["r1_std"] or 0,
               entry["n_trainable_params"] or 0, entry["vision_nonzero_tensors"],
               entry["vision_rank_delta_mean"] or 0, entry["text_rank_delta_mean"] or 0))

    # legacy comparison
    summary["legacy"] = {}
    print("\nlegacy (mixed convention, for comparison)")
    for label, rel in LEGACY:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        d = load(rel)
        a, b = cg(d, "initial_gap"), cg(d, "final_gap")
        summary["legacy"][label] = {
            "n_trainable_params": d.get("n_trainable_params"),
            "cg_delta": (b - a) if (a is not None and b is not None) else None,
            "r1": r1(d),
        }
        e = summary["legacy"][label]
        print("  %-24s trainable=%s  CG delta=%s  R@1=%s" %
              (label, e["n_trainable_params"],
               "%.4f" % e["cg_delta"] if e["cg_delta"] is not None else "-",
               "%.4f" % e["r1"] if e["r1"] is not None else "-"))

    # LaTeX-ready rows
    print("\n%% --- LaTeX rows ---")
    for tag, e in summary["configs"].items():
        if e["n_seeds"] < 1:
            continue
        print(" %s & %d & %d & $%+.3f \\pm %.3f$ & %.3f & %s \\\\" % (
            tag.replace("_", "-"), e["n_seeds"], e["n_trainable_params"],
            e["cg_delta_mean"], e["cg_delta_std"], e["r1_mean"],
            ("%d/%d" % (e["vision_nonzero_tensors"][0], e["vision_tensors"]))
            if e["vision_nonzero_tensors"] else "?"))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

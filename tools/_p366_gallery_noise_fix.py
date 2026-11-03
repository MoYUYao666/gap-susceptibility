# -*- coding: utf-8 -*-
r"""p366 -- diagnose + repair the rev-1 gallery-noise run (vision LoRA active during init).

BUG (mine, rev-1 of tools/_p360_gallery_noise.py)
    `load_lora_state()` loads A and B for EVERY injected layer.  In the arm loop I then
    zeroed only the TEXT keys' B before the init pass, so for the arms that also inject
    into the vision tower (`both`, `vision_only`) the init pass was measured with the
    ADAPTED vision tower.  Therefore, for those two arms only:
        CG_init / DG_init / R1_init  and every field derived from them (dCG, dDG, dR1)
    are NOT the protocol's step-0 quantities.
    The FINAL values (CG_final / DG_final / R1_final) are unaffected and correct.

    The fix is exact, not approximate: the step-0 model is the same pristine backbone for
    every arm, and `aug_loader(ds, idx, r)` uses the identical per-item seeding for every
    arm, so `CG_init(r)` of the `text_only` arm IS the step-0 value the `both` /
    `vision_only` arms should be differenced against in draw r.

This script
  1. re-reads the archived CLIP seed42 results to show what the protocol's own Delta-CG is,
  2. rebuilds the corrected per-draw Delta-CG / Delta-R@1 for every arm from the rev-1 JSON,
  3. reports paired (same draw) and protocol-faithful (init draw != final draw) spreads,
  4. writes outputs/analysis/dinov2_hetero/gallery_noise/results_corrected.json

    python tools/_p366_gallery_noise_fix.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GN = REPO / "outputs" / "analysis" / "dinov2_hetero" / "gallery_noise" / "results.json"
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "gallery_noise" / "results_corrected.json"


def stat(v):
    return {"n": len(v), "mean": statistics.mean(v),
            "sd": statistics.stdev(v) if len(v) > 1 else None,
            "min": min(v), "max": max(v), "range": max(v) - min(v)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rep = {"script": "tools/_p366_gallery_noise_fix.py",
           "why": "rev-1 of _p360 left the vision LoRA active during the init pass for the "
                  "vision-side arms.  In practice only DRAW 0 was affected, because the loop "
                  "zeroes the vision B at the end of every draw, so draws 1..N-1 already "
                  "differenced against the pristine tower (verified: their CG_init equals the "
                  "text_only arm's CG_init draw-for-draw).  This script rebuilds every arm's "
                  "init against the text_only CG_init series, which is exact for all draws "
                  "because the step-0 model and the per-item augmentation seed are identical "
                  "across arms.",
           "archived_seed42": {}, "corrected": {}, "protocol_note": {}}

    for arm in ("text_only", "both", "vision_only"):
        p = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "results.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        rep["archived_seed42"][arm] = {
            "source": str(p.relative_to(REPO)),
            "CG_initial": d["initial_gap"]["centroid_gap"],
            "CG_final": d["final_gap"]["centroid_gap"],
            "delta_CG": d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"],
            "R1_initial_unrecorded": ("the trainer records no step-0 R@1; only the final "
                                      "task metrics are archived"),
            "R1_final": d["final_task_metrics"]["R@1"],
        }

    if not GN.exists():
        print("no rev-1 JSON yet at %s" % GN)
        return 1
    g = json.loads(GN.read_text(encoding="utf-8"))
    arms = g["arms"]
    base = arms["clip_b32_text_only"]["draws"]           # pristine step-0 series per draw
    cg0 = base["CG_init"]["values"]
    dg0 = base["DG_init"]["values"]
    r10 = base["R1_init"]["values"]

    # ---- the DINOv2 heterogeneous arm has NO pristine step-0 series in rev-1 (same defect:
    # its own text LoRA was already loaded when T_init was computed), so its init is taken
    # from the archived frozen re-measurement of the augmented gallery.
    frozen_aug = None
    npj = REPO / "outputs" / "analysis" / "dinov2_hetero" / "norm_probe" / "results.json"
    if npj.exists():
        npj_d = json.loads(npj.read_text(encoding="utf-8"))
        frozen_aug = npj_d["frozen"]["clip_aug_r0"]
    dinov2_key = "dinov2_het_text_only_seed42"
    if frozen_aug is not None and dinov2_key in arms:
        rec_extra = {
            "init_source": "outputs/analysis/dinov2_hetero/norm_probe/results.json "
                           ":: frozen.clip_aug_r0 (augmented gallery, pristine model, "
                           "same head) -- used because rev-1 computed this arm's T_init "
                           "with the adapted text LoRA already loaded",
            "CG_init_assumed": frozen_aug["CG"], "DG_init_assumed": frozen_aug["DG"],
            "R1_init_assumed": frozen_aug["R@1"],
            "CG_init_draw_noise_measured_elsewhere": ("the frozen CG's draw-to-draw sd is "
                                                      "~0.0005 (clip_aug_r0 vs clip_aug_r1 in "
                                                      "norm_probe: 0.6767 vs 0.6768)"),
        }
    else:
        rec_extra = {}

    for name, rec in arms.items():
        d = rec["draws"]
        cg_f, dg_f, r1_f = d["CG_final"]["values"], d["DG_final"]["values"], d["R1_final"]["values"]
        n = len(cg_f)
        if name == dinov2_key and frozen_aug is not None:
            init_cg = [frozen_aug["CG"]] * n
            init_dg = [frozen_aug["DG"]] * n
            init_r1 = [frozen_aug["R@1"]] * n
        else:
            init_cg, init_dg, init_r1 = cg0[:n], dg0[:n], r10[:n]
        # protocol-faithful: final of draw r against the step-0 of a DIFFERENT draw
        # (the trainer measures initial at epoch 0 and final at epoch 10 -> independent draws)
        cg0_shift = init_cg[1:] + init_cg[:1] if len(init_cg) > 1 else init_cg
        entry = {
            "source_json": str(GN.relative_to(REPO)),
            "n_draws": n,
            "init_state_used_for_correction": (
                "archived frozen re-measurement (augmented draw)" if name == dinov2_key
                else "clip_b32_text_only CG_init series (identical pristine step-0 model, "
                     "identical per-item augmentation seed per draw)"),
            **rec_extra,
            "CG_final": stat(cg_f),
            "R1_final": stat(r1_f),
            "DG_final": stat(dg_f),
            "delta_CG_paired_same_draw": stat([f - i for f, i in zip(cg_f, init_cg)]),
            "delta_CG_protocol_independent_draws": stat([f - i for f, i in zip(cg_f, cg0_shift)]),
            "delta_R1_paired_same_draw": stat([f - i for f, i in zip(r1_f, init_r1)]),
            "raw_rev1_dCG_is_invalid_for_this_arm": bool(
                rec.get("visual_side_perturbed") or name == dinov2_key),
            "raw_rev1_dCG_mean": d["dCG"]["mean"],
            "archived_delta_CG": rec.get("archived", {}).get("delta_CG"),
            "archived_R1": rec.get("archived", {}).get("R1"),
        }
        rep["corrected"][name] = entry

    # how much of the noise is shared between init and final draws?
    rep["protocol_note"] = {
        "delta_CG_sd_same_draw_vs_independent": {
            k: {"same_draw_sd": v["delta_CG_paired_same_draw"]["sd"],
                "independent_sd": v["delta_CG_protocol_independent_draws"]["sd"]}
            for k, v in rep["corrected"].items()},
        "paper_arm_separation_delta_CG": {
            "source": "outputs/analysis/dinov2_hetero/clip_baseline_check.json :: rows "
                      "'CLIP B/32 r8' published",
            "text_only_minus_both": -0.0465 - (-0.0258),
            "both_minus_vision_only": -0.0258 - 0.0106,
        },
        "paper_R1_separation": {"text_only_vs_both": 0.693 - 0.624,
                                "both_vs_vision_only": 0.693 - 0.680},
    }

    print(json.dumps(rep, indent=2, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

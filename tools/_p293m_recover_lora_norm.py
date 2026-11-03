# -*- coding: utf-8 -*-
r"""Recover the LoRA update magnitude for the seed42 text_only arm from its checkpoint.

The first `text_only/seed42` run predates the `lora_update_norm_frobenius` instrumentation, and
its in-JSON `backbone_delta` is 0 by construction (pre-existing weights are frozen under the
strict-freeze control).  The adaptation magnitude is however recoverable, because
`best_checkpoint.pt` stores the trained LoRA A/B matrices.

`src/trainer.py::_save_checkpoint` writes:
    {"lora_state_dict": {layer_name: {"A": lora_A.data, "B": lora_B.data}}, ...}
and `src/lora.py::LoRALinear` computes the effective update as `scaling * x @ A @ B` with
`scaling = alpha / rank`.  This script therefore reports, per tower and in total,
    ||scaling * A @ B||_F     (and the max |.| entry)
which is exactly the quantity the new instrumentation measures, so the seed42 arm can be
compared with the later arms without a rerun.

OUTPUT
    outputs/analysis/dinov2_hetero/fitted/text_only/seed42/lora_norm_recovered.json

USAGE
    python tools/_p293m_recover_lora_norm.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)

import torch  # noqa: E402

RUNS = [
    ("fitted", "text_only", 42),
    ("fitted", "both", 42),
    ("fitted", "vision_only", 42),
    ("random", "text_only", 42),
    ("random", "both", 42),
    ("random", "vision_only", 42),
]

OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "lora_norm_recovered_all.json"


def run_dir(head, arm, seed):
    return (REPO / "outputs" / "analysis" / "dinov2_hetero" / head / arm
            / ("seed%d" % seed))


def main():
    out_all = {
        "script": "tools/_p293m_recover_lora_norm.py",
        "why": ("runs started before the lora_update_* instrumentation was fixed carry 0.0 in "
                "those fields, because the pre-fix code zeroed the trained LoRA matrices before "
                "measuring them; the trained matrices survive in the run's checkpoints, so the "
                "same quantity is recoverable without a rerun"),
        "note": ("computed from the checkpoint, NOT measured in-process -- distinguished on "
                 "purpose so the report never implies the field existed at run time"),
        "runs": {},
    }
    for head, arm, seed in RUNS:
        rd = run_dir(head, arm, seed)
        if not (rd / "results.json").exists():
            continue
        res = json.loads((rd / "results.json").read_text(encoding="utf-8"))
        scaling = res["alpha"] / res["rank"]
        rec = {"scaling_alpha_over_rank": scaling}
        for which in ("best", "last"):
            ck = rd / ("%s_checkpoint.pt" % which)
            if ck.exists():
                rec[which] = analyse(ck, scaling)
        if len(rec) <= 1:
            continue
        outp = rd / "lora_norm_recovered.json"
        outp.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        key = "%s/%s/seed%d" % (head, arm, seed)
        out_all["runs"][key] = {"file": str(outp.relative_to(REPO)).replace("\\", "/"),
                                "values": rec.get("best")}
        print("=== %s ===" % key)
        print("  frobenius_of_scaled_update:",
              rec["best"]["frobenius_of_scaled_update"]["value"],
              rec["best"]["frobenius_of_scaled_update"]["definition"])
        print("  sum_of_per_layer_frobenius:",
              rec["best"]["sum_of_per_layer_frobenius"]["value"],
              "mean %.4f/layer" % rec["best"]["sum_of_per_layer_frobenius"]["per_layer_mean"])

    (OUT.parent / "lora_norm_recovered_all.json").write_text(
        json.dumps(out_all, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n[ok] wrote", OUT.parent / "lora_norm_recovered_all.json")


def analyse(path: Path, alpha_over_rank: float):
    ck = torch.load(path, weights_only=False)
    sd = ck["lora_state_dict"]
    norms, maxabs, layers = {}, {}, {}
    sum_of_layer_norms, sum_unscaled_layer_norms = 0.0, 0.0
    for name, ab in sd.items():
        A = ab["A"].float()
        B = ab["B"].float()
        delta = alpha_over_rank * (A @ B)      # (in, out); scaling * A @ B
        grp = "vision" if name.startswith("vision") else "text"
        norms[grp] = norms.get(grp, 0.0) + float(delta.norm().item()) ** 2
        maxabs[grp] = max(maxabs.get(grp, 0.0), float(delta.abs().max().item()))
        layers[grp] = layers.get(grp, 0) + 1
        sum_of_layer_norms += float(delta.norm().item())
        sum_unscaled_layer_norms += float((A @ B).norm().item())
    n_layers = sum(layers.values())
    return {
        "checkpoint": str(path.relative_to(REPO)).replace("\\", "/"),
        "epoch": ck.get("epoch"),
        "n_lora_layers": layers,
        # TWO DIFFERENT AGGREGATES -- both defensible, neither interchangeable, so both are
        # emitted with their definitions.  A reviewer comparing this run with the later arms must
        # pick one and use it for all of them.
        "frobenius_of_scaled_update": {
            "definition": "sqrt(sum_layers ||scaling*A@B||_F^2)",
            "value": round(sum(norms.values()) ** 0.5, 4)},
        "sum_of_per_layer_frobenius": {
            "definition": "sum_layers ||scaling*A@B||_F   (NOT a norm of any single matrix)",
            "value": round(sum_of_layer_norms, 4),
            "per_layer_mean": round(sum_of_layer_norms / n_layers, 4)},
        "sum_of_per_layer_frobenius_unscaled": {
            "definition": "sum_layers ||A@B||_F, i.e. without the alpha/rank factor",
            "value": round(sum_unscaled_layer_norms, 4)},
        "max_abs": {g: round(v, 6) for g, v in maxabs.items()},
    }


if __name__ == "__main__":
    main()

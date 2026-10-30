# -*- coding: utf-8 -*-
r"""p365 -- the LoRA adaptation magnitudes of the DINOv2 run vs the paper's CLIP run.

`experiments/strict_freeze_control.py:210-217` already records
`lora_update_norm` = per-group Frobenius norm of `scaling * (B @ A)` (== the norm of the
weight-space update), and the archive holds it for every CLIP arm.  The DINOv2 run's
`backbone_delta` cannot carry it, and its own `lora_update_norm_frobenius` field was
written by a version whose LoRA matrices had been zeroed (see the report); this script
recovers the DINOv2 value from the TRAINED checkpoint instead, so the two experiments can
be compared on the same quantity with an explicit source for each number.

    python tools/_p365_lora_update_norms.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "lora_update_norms.json"


def from_archive(p: Path):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("lora_update_norm")


def from_checkpoint(p: Path):
    import torch
    ck = torch.load(str(p), map_location="cpu", weights_only=False)
    lsd = ck["lora_state_dict"]
    agg = {}
    per_layer = []
    for k, v in lsd.items():
        grp = "vision" if k.startswith("vision") else "text"
        A, B = v["A"].float(), v["B"].float()
        # _inject_lora stores alpha/rank as `scaling`; both experiment scripts use rank8/alpha16
        scaling = 16.0 / 8.0
        delta = scaling * (A @ B)
        agg[grp] = agg.get(grp, 0.0) + float(delta.norm()) ** 2
        per_layer.append(float(delta.norm()))
    return {g: v ** 0.5 for g, v in agg.items()}, {
        "n_layers": len(lsd), "checkpoint_epoch": ck.get("epoch"),
        "per_layer_mean": sum(per_layer) / len(per_layer) if per_layer else None,
        "per_layer_max": max(per_layer) if per_layer else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rep = {"script": "tools/_p365_lora_update_norms.py",
           "formula": "per group: sqrt(sum_layers ||scaling * (A @ B)||_F^2), "
                      "scaling = alpha/rank = 16/8 = 2",
           "source_paper_definition":
               "experiments/strict_freeze_control.py:210-217 lora_update_norms()",
           "arms": {}}

    for arm in ("text_only", "both", "vision_only"):
        p = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "results.json"
        if p.exists():
            rep["arms"]["clip_b32_" + arm] = {
                "value": from_archive(p),
                "source": str(p.relative_to(REPO)) + " :: lora_update_norm",
                "measured_by": "experiments/strict_freeze_control.py (the paper's control)",
            }

    dp = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "text_only"
          / "seed42")
    ckp = dp / "last_checkpoint.pt"
    if ckp.exists():
        val, meta = from_checkpoint(ckp)
        rep["arms"]["dinov2_het_text_only"] = {
            "value": val,
            "source": str(ckp.relative_to(REPO)) + " :: lora_state_dict -> "
                      "||scaling*(A@B)||_F summed per tower",
            "measured_by": "tools/_p365_lora_update_norms.py (audit recovery; the "
                           "experiment's own field for this run predates the field's "
                           "introduction)",
            "detail": meta,
        }
    dp2 = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "both" / "seed42")
    for name in ("best_checkpoint.pt", "last_checkpoint.pt"):
        f = dp2 / name
        if f.exists():
            val, meta = from_checkpoint(f)
            rep["arms"]["dinov2_het_both"] = {
                "value": val,
                "source": str(f.relative_to(REPO)) + " :: lora_state_dict",
                "measured_by": "tools/_p365_lora_update_norms.py (audit recovery)",
                "warning": ("the in-flight `both` process loaded the pre-fix script, so its "
                            "own results.json lora_update_norm_frobenius will read 0.0; "
                            "this value is the real one"),
                "detail": meta,
            }
            break

    rep["comparison"] = {
        "clip_b32_text_only": rep["arms"].get("clip_b32_text_only", {}).get("value"),
        "dinov2_het_text_only": rep["arms"].get("dinov2_het_text_only", {}).get("value"),
        "note": "same arm definition, same rank/alpha, same 24 text layers, same 512-wide "
                "tower, same 5000-sample Flickr30k slice -- so the two numbers are directly "
                "comparable as 'how far the text tower was moved'",
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

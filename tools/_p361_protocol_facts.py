# -*- coding: utf-8 -*-
r"""p361 -- protocol-comparability facts that the DINOv2 audit needs, from source files only.

CPU, seconds.  Prints (and optionally writes) hard facts with their source:
  * CLIP B/32's pretrained `logit_scale` vs the constant the DINOv2 script hardcodes
    (2.659260036932778) -- the DINOv2 script says it holds the CLIP value fixed
  * DINOv2-base's shipped preprocessor geometry vs what src/dataset.py feeds it
  * trainable-parameter counts per arm, closed form vs the archives

    python tools/_p361_protocol_facts.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "protocol_facts.json"

DINOV2_CONST = 2.659260036932778


def lora_params(hidden, layers, rank):
    return layers * 2 * (hidden * rank + rank * hidden)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rep = {"script": "tools/_p361_protocol_facts.py", "facts": {}}

    # ---- 1. logit_scale -------------------------------------------------------
    import torch
    from transformers import CLIPModel
    m = CLIPModel.from_pretrained(str(REPO / "models" / "clip-vit-base-patch32"),
                                  local_files_only=True)
    ls = float(m.logit_scale.detach().float().item())
    rep["facts"]["clip_b32_logit_scale"] = {
        "value": ls,
        "ln_1_over_0.07": math.log(1 / 0.07),
        "dinov2_script_constant": DINOV2_CONST,
        "equal_to_dinov2_constant": abs(ls - DINOV2_CONST) < 1e-12,
        "source_model": "models/clip-vit-base-patch32 (logit_scale parameter)",
        "source_script": "tools/_p293_dinov2_hetero_strict.py:108 LOGIT_SCALE_INIT",
        "why_it_matters": ("the strict-freeze control freezes every parameter except LoRA "
                           "A/B, so this pretrained value is the temperature both experiments "
                           "train under; it does not enter CG/DG/R@1 at all"),
    }
    del m

    # ---- 2. DINOv2 preprocessor ----------------------------------------------
    import json as _json
    pp = _json.loads((REPO / "models" / "dinov2-base" / "preprocessor_config.json")
                     .read_text(encoding="utf-8"))
    rep["facts"]["dinov2_preprocessor"] = {
        "path": "models/dinov2-base/preprocessor_config.json",
        "image_mean": pp["image_mean"], "image_std": pp["image_std"],
        "size": pp["size"], "crop_size": pp["crop_size"], "resample": pp["resample"],
        "do_center_crop": pp["do_center_crop"], "do_rescale": pp["do_rescale"],
        "note": ("shortest_edge 256 -> centre-crop 224 is DINOv2's own eval geometry, so "
                 "image_size=224 is NOT an out-of-distribution resolution by itself; the "
                 "mean/std differ from CLIP's and src/dataset.py:19-20 uses CLIP's"),
    }
    rep["facts"]["clip_preprocessor"] = {
        "source": "src/dataset.py:19-20 CLIP_MEAN/CLIP_STD used for every image",
        "clip_mean": [0.48145466, 0.4578275, 0.40821073],
        "clip_std": [0.26862954, 0.26130258, 0.27577711],
        "geometry": "Resize((224,224), BICUBIC)  -- note: not the shortest-edge-256 crop "
                    "that either model's own preprocessor uses",
    }

    # ---- 3. parameter budgets ------------------------------------------------
    rep["facts"]["trainable_params_closed_form"] = {
        "clip_b32": {"text_side_512x12": lora_params(512, 12, 8),
                     "vision_side_768x12": lora_params(768, 12, 8)},
        "dinov2_base": {"text_side_512x12": lora_params(512, 12, 8),
                        "vision_side_768x12": lora_params(768, 12, 8)},
        "note": "both towers are 12-layer, text hidden 512, vision hidden 768",
    }
    rep["facts"]["trainable_params_from_archive"] = {
        "source_clip": "outputs/strict_freeze/{text_only,both,vision_only}/seed42/results.json"
                       " :: n_trainable_params",
        "source_dinov2": "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/results.json"
                         " :: n_trainable_params / n_trainable_vision_side /"
                         " n_trainable_text_side",
    }
    vals = {}
    for arm in ("text_only", "both", "vision_only"):
        p = REPO / "outputs" / "strict_freeze" / arm / "seed42" / "results.json"
        vals["clip_" + arm] = _json.loads(p.read_text(encoding="utf-8"))["n_trainable_params"]
    p = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / "text_only"
         / "seed42" / "results.json")
    d = _json.loads(p.read_text(encoding="utf-8"))
    vals["dinov2_text_only"] = d["n_trainable_params"]
    vals["dinov2_text_side"] = d["n_trainable_text_side"]
    vals["dinov2_vision_side"] = d["n_trainable_vision_side"]
    rep["facts"]["trainable_params_from_archive"]["values"] = vals

    # ---- 4. the archived frozen reference -----------------------------------
    fr = _json.loads((REPO / "outputs" / "strict_freeze" / "frozen" / "results.json")
                     .read_text(encoding="utf-8"))
    rep["facts"]["paper_frozen_reference"] = {
        "path": "outputs/strict_freeze/frozen/results.json",
        "keys": sorted(fr.keys()),
        "has_CG": "CG" in fr, "has_DG": "DG" in fr, "has_R1": "R@1" in fr,
        "why_it_matters": ("the paper's strict-freeze control records no frozen-baseline "
                           "CG/DG/R@1 at all (experiments/strict_freeze_control.py:312-339 "
                           "only writes effective rank + backbone_delta), so the paper's "
                           "Delta-CG column is a within-run final-minus-initial quantity and "
                           "the frozen model's retrieval has no archive source"),
    }

    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

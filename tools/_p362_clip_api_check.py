# -*- coding: utf-8 -*-
r"""p362 -- why does CLIPModel.get_text_features return a ModelOutput here?

Diagnostic only (CPU, ~20 s).  Records: which transformers is imported, its version and
file, and what get_text_features / get_image_features return -- before and after
`src.lora.apply_lora_to_model`.

    python tools/_p362_clip_api_check.py --apply
"""
from __future__ import annotations

import argparse
import inspect
import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "clip_api_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import transformers
    from transformers import CLIPModel

    rep = {"script": "tools/_p362_clip_api_check.py",
           "transformers_version": transformers.__version__,
           "transformers_file": transformers.__file__,
           "torch": torch.__version__,
           "sys_path_head": sys.path[:6], "observations": {}}

    src = inspect.getsource(CLIPModel.get_text_features)
    rep["observations"]["get_text_features_source"] = src
    rep["observations"]["get_text_features_source_file"] = inspect.getsourcefile(
        CLIPModel.get_text_features)

    mp = str(REPO / "models" / "clip-vit-base-patch32")
    model = CLIPModel.from_pretrained(mp, local_files_only=True).eval()
    ids = torch.zeros((2, 77), dtype=torch.long)
    am = torch.ones((2, 77), dtype=torch.long)

    t = model.get_text_features(input_ids=ids, attention_mask=am)
    rep["observations"]["before_injection_type"] = type(t).__name__
    rep["observations"]["before_injection_is_tensor"] = torch.is_tensor(t)
    if not torch.is_tensor(t):
        rep["observations"]["before_injection_fields"] = list(t.keys())
    im = model.get_image_features(pixel_values=torch.zeros((2, 3, 224, 224)))
    rep["observations"]["before_injection_image_type"] = type(im).__name__

    from src.lora import apply_lora_to_model
    model, layers, n = apply_lora_to_model(model, rank=8, alpha=16, dropout=0.0,
                                           target_modules=["q_proj", "v_proj"],
                                           apply_to_vision=False, apply_to_text=True)
    model.eval()
    t2 = model.get_text_features(input_ids=ids, attention_mask=am)
    rep["observations"]["after_injection_type"] = type(t2).__name__
    rep["observations"]["after_injection_is_tensor"] = torch.is_tensor(t2)
    if not torch.is_tensor(t2):
        rep["observations"]["after_injection_fields"] = list(t2.keys())
    rep["observations"]["n_lora_layers"] = len(layers)
    # does the forward path still work?
    out = model(pixel_values=torch.zeros((2, 3, 224, 224)), input_ids=ids,
                attention_mask=am)
    rep["observations"]["forward_has_text_embeds"] = hasattr(out, "text_embeds")
    rep["observations"]["forward_text_embeds_type"] = type(out.text_embeds).__name__

    print(json.dumps(rep, indent=1, ensure_ascii=False)[:4000])
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

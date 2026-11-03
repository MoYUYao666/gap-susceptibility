# -*- coding: utf-8 -*-
r"""Post-hoc metrics for the caption downstream check: token F1 and CLIP image-caption similarity.

    python tools/_p1504_p3_caption_metrics.py
"""
from __future__ import annotations

import collections
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
IMAGES = os.path.join(REPO, "data", "marine_captions")
MODEL = os.path.join(REPO, "models", "clip-vit-base-patch32")


def token_f1(refs, hyps) -> float:
    f1s = []
    for r, h in zip(refs, hyps):
        rt = reference = collections.Counter(r.lower().split())
        ht = collections.Counter(h.lower().split())
        common = sum((rt & ht).values())
        if common == 0:
            f1s.append(0.0)
        else:
            p = common / max(sum(ht.values()), 1)
            rec = common / max(sum(rt.values()), 1)
            f1s.append(2 * p * rec / (p + rec))
    return sum(f1s) / len(f1s)


def main() -> int:
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained(MODEL).eval()
    proc = CLIPProcessor.from_pretrained(MODEL)
    out = {}
    for f in sorted(glob.glob(os.path.join(AN, "p3_caption_downstream_*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        key = str(d.get("rank"))
        refs, hyps = d["refs"], d["hypotheses"]
        sims = []
        for i, h in enumerate(hyps):
            img = Image.open(os.path.join(IMAGES, f"{i:04d}.jpg")).convert("RGB")
            inp = proc(text=[h], images=img, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                o = model(**inp)
                img_e = o.image_embeds / o.image_embeds.norm(dim=-1, keepdim=True)
                txt_e = o.text_embeds / o.text_embeds.norm(dim=-1, keepdim=True)
                sims.append(float((img_e * txt_e).sum()))
        out[key] = {"bleu4": d.get("bleu4"), "exact_match": d.get("exact_match"),
                    "token_f1": token_f1(refs, hyps), "clip_sim_mean": sum(sims) / len(sims),
                    "n_eval": len(refs), "hypotheses": hyps, "refs": refs}
        print(key, out[key]["bleu4"], round(out[key]["token_f1"], 4), round(out[key]["clip_sim_mean"], 4))
    p = os.path.join(AN, "p3_caption_metrics.json")
    io.open(p, "w", encoding="utf-8", newline="").write(json.dumps({"meta": {"script": "tools/_p1504_p3_caption_metrics.py"},
                                                                     "arms": out}, indent=1))
    print("wrote", os.path.relpath(p, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

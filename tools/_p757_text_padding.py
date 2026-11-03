# -*- coding: utf-8 -*-
r"""Check whether caption padding is corrupting the CLIP text embeddings.

On 10,000 COCO val images with the corrected protocol, image->text R@1 is 0.9957 while text->image
R@1 is 0.1584. The image side cannot be that good and the text side that bad; the asymmetry points
at the text encoder. CLIP's text tower uses causal attention and, when padding is applied on the
left (or when the pooled output is taken at the wrong position), padding tokens enter the attention
computation and the pooled embedding is taken from a padded position.

This compares the text embeddings under different padding settings against a reference computed one
caption at a time, which needs no padding at all.

    python tools/_p757_text_padding.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "text_padding_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=128)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor, CLIPTokenizerFast

    device = "cuda" if torch.cuda.is_available() else "cpu"
    mid = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(mid).to(device).eval()
    proc = CLIPProcessor.from_pretrained(mid)
    tok = CLIPTokenizerFast.from_pretrained(mid)
    print(f"  tokenizer padding_side = {tok.padding_side}")

    caps = [
        "A man riding a wave on top of a surfboard.",
        "A dog",
        "Two people standing next to each other in front of a building with many windows and a red door",
        "A plate of food on a wooden table with a glass of wine beside it",
    ] * (a.n // 4)

    def embed(pad_mode):
        if pad_mode == "one_by_one":
            embs = []
            with torch.no_grad():
                for c in caps:
                    t = tok([c], return_tensors="pt", padding=False, truncation=True, max_length=77)
                    o = model.get_text_features(input_ids=t["input_ids"].to(device),
                                                attention_mask=t["attention_mask"].to(device))
                    embs.append(F.normalize(o if torch.is_tensor(o) else o.pooler_output,
                                            p=2, dim=-1).cpu())
            return torch.cat(embs)
        kw = dict(return_tensors="pt", truncation=True, max_length=77)
        if pad_mode == "max_length":
            t = tok(caps, padding="max_length", **kw)
        else:
            t = tok(caps, padding=True, **kw)
        with torch.no_grad():
            o = model.get_text_features(input_ids=t["input_ids"].to(device),
                                        attention_mask=t["attention_mask"].to(device))
            o = o if torch.is_tensor(o) else o.pooler_output
        return F.normalize(o, p=2, dim=-1).cpu()

    ref = embed("one_by_one")
    res = {}
    print()
    print("=" * 96)
    print("agreement with the per-caption reference embedding")
    print("=" * 96)
    for mode in ("one_by_one", "padding=True", "max_length"):
        e = embed(mode)
        cos = F.cosine_similarity(ref, e, dim=-1)
        res[mode] = {"min_cos": float(cos.min()), "mean_cos": float(cos.mean())}
        print(f"  {mode:<14} min cos = {float(cos.min()):.4f}   mean cos = {float(cos.mean()):.4f}")

    print()
    print("=" * 96)
    print("a small retrieval test: 4 captions against their own batch")
    print("=" * 96)
    caps4 = caps[:4]
    with torch.no_grad():
        imgs = [torch.zeros(3, 224, 224)] * 4
        t_max = tok(caps4, padding="max_length", return_tensors="pt", truncation=True, max_length=77)
        o_max = model.get_text_features(input_ids=t_max["input_ids"].to(device),
                                       attention_mask=t_max["attention_mask"].to(device))
        o_max = F.normalize(o_max if torch.is_tensor(o_max) else o_max.pooler_output, p=2, dim=-1)
        t_tru = tok(caps4, padding=True, return_tensors="pt", truncation=True, max_length=77)
        o_tru = model.get_text_features(input_ids=t_tru["input_ids"].to(device),
                                       attention_mask=t_tru["attention_mask"].to(device))
        o_tru = F.normalize(o_tru if torch.is_tensor(o_tru) else o_tru.pooler_output, p=2, dim=-1)
    print(f"  mean |max_length - padding=True| = "
          f"{float((o_max - o_tru).abs().mean()):.6f}")
    print(f"  max  |max_length - padding=True| = "
          f"{float((o_max - o_tru).abs().max()):.6f}")
    print(f"  caption lengths: {[len(tok(c)['input_ids']) for c in caps4]}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

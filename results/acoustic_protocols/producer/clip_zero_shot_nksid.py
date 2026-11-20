# -*- coding: utf-8 -*-
"""Zero-shot NKSID classification with the frozen RemoteCLIP ViT-B/32 baseline, same subset as the small-VLM runs.

The subset, class list and prompt are the ones used in small_vlm_zero_shot.py, so the numbers are directly comparable:
for each class a text prompt ("a forward-looking sonar image of <class>") is embedded, images are embedded once, and
the prediction is nearest text embedding.

Run with --help for required input and output paths.
"""
import argparse
import io
import json
import os
import random


CLASSES = ["big_propeller", "cylinder", "fishing_net", "floats", "iron_pipeline", "small_propeller", "soft_pipeline"]
PRETTY = {c: c.replace("_", " ") for c in CLASSES}


def build(images_root, per_class, seed):
    rng = random.Random(seed)
    items = []
    for c in CLASSES:
        d = os.path.join(images_root, c)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".png", ".jpeg")))
        rng.shuffle(files)
        items += [(os.path.join(d, f), c) for f in files[:per_class]]
    rng.shuffle(items)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--images-root", required=True, help="Directory containing the seven class folders")
    ap.add_argument("--checkpoint", required=True, help="External local model file or snapshot directory")
    ap.add_argument("--output", required=True, help="Path for a new result JSON")
    args = ap.parse_args()
    if os.path.exists(args.output):
        ap.error("--output already exists")
    global torch, Image
    import torch
    from PIL import Image
    import open_clip

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained=args.checkpoint,
        precision="fp32", device=device)
    model.eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    prompts = ["a forward-looking sonar image of a " + PRETTY[c] for c in CLASSES]
    with torch.inference_mode():
        text_emb = model.encode_text(tokenizer(prompts).to(device))
        text_emb = torch.nn.functional.normalize(text_emb.float(), dim=-1)

    items = build(args.images_root, args.per_class, args.seed)
    correct = 0
    confusion = {c: {d: 0 for d in CLASSES} for c in CLASSES}
    for i, (path, truth) in enumerate(items):
        with Image.open(path) as im:
            pixel = preprocess(im.convert("RGB")).unsqueeze(0).to(device)
        with torch.inference_mode():
            emb = model.encode_image(pixel)
            emb = torch.nn.functional.normalize(emb.float(), dim=-1)
        pred = CLASSES[int((emb @ text_emb.t()).argmax())]
        confusion[truth][pred] += 1
        correct += int(pred == truth)
    n = sum(sum(row.values()) for row in confusion.values())
    per_class = {}
    for c in CLASSES:
        total = sum(confusion[c].values())
        per_class[c] = round(confusion[c][c] / total, 4) if total else None
    macro = round(sum(v for v in per_class.values() if v is not None) / len(per_class), 4)
    payload = {"model": "remoteclip_vit_b32_frozen", "images": n, "per_class_cap": args.per_class,
               "correct": correct, "accuracy": round(correct / n, 4), "macro_accuracy": macro,
               "chance": round(1 / len(CLASSES), 4), "per_class": per_class, "confusion": confusion,
               "prompts": prompts}
    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, "x", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("CLIP zero-shot: accuracy %.4f | macro %.4f | n %d | chance %.3f" % (correct / n, macro, n, 1 / len(CLASSES)))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

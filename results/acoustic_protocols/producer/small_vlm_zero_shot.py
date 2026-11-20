# -*- coding: utf-8 -*-
"""Small-VLM zero-shot baseline on the NKSID sonar classification set (A2 follow-up).

Two small models are evaluated (Qwen3-VL-2B-Instruct and SmolVLM2-2.2B-Instruct): each image is shown once with a
fixed prompt listing the seven NKSID classes, and the answer is mapped to the class whose name appears first.

A stratified subset is used (at most `--per-class` images per class, fishing_net has only 20), so the numbers are
comparable across models and cheap to reproduce. Output: paper_a2/analysis/smallvlm_nksid_<model>.json

Run with --help for required input and output paths.
"""
import argparse
import io
import json
import os
import random
import time


CLASSES = ["big_propeller", "cylinder", "fishing_net", "floats", "iron_pipeline", "small_propeller",
           "soft_pipeline"]
PRETTY = {c: c.replace("_", " ") for c in CLASSES}
PROMPT = ("This is a forward-looking sonar image. Which object does it show? Choose exactly one option from this "
          "list and answer with that option only: " + "; ".join(PRETTY[c] for c in CLASSES) + ".")


def build(path, per_class, seed):
    rng = random.Random(seed)
    items = []
    for c in CLASSES:
        d = os.path.join(path, c)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".png", ".jpeg")))
        rng.shuffle(files)
        for f in files[:per_class]:
            items.append((os.path.join(d, f), c))
    rng.shuffle(items)
    return items


def parse(answer):
    low = answer.lower()
    hits = [(low.find(PRETTY[c]), c) for c in CLASSES if PRETTY[c] in low]
    hits = [h for h in hits if h[0] >= 0]
    return min(hits)[1] if hits else None


def load_qwen(model_dir, device):
    from transformers import AutoProcessor, AutoModelForImageTextToText
    processor = AutoProcessor.from_pretrained(model_dir)
    model = AutoModelForImageTextToText.from_pretrained(model_dir, dtype=torch.bfloat16, device_map=device)
    model.eval()
    return processor, model


def load_smol(model_dir, device):
    from transformers import AutoProcessor, AutoModelForImageTextToText
    processor = AutoProcessor.from_pretrained(model_dir)
    model = AutoModelForImageTextToText.from_pretrained(model_dir, dtype=torch.bfloat16, device_map=device)
    model.eval()
    return processor, model


def answer_qwen(processor, model, image):
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=[prompt], images=[image], return_tensors="pt").to(model.device)
    with torch.inference_mode():
        gen = model.generate(**inputs, max_new_tokens=16, do_sample=False)
    trimmed = gen[0][inputs["input_ids"].shape[1]:]
    return processor.decode(trimmed, skip_special_tokens=True).strip()


def answer_smol(processor, model, image):
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="pt").to(model.device)
    with torch.inference_mode():
        gen = model.generate(**inputs, max_new_tokens=16, do_sample=False)
    trimmed = gen[0][inputs["input_ids"].shape[1]:]
    return processor.decode(trimmed, skip_special_tokens=True).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["qwen3vl2b", "smolvlm2", "internvl35_2b"])
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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.model == "internvl35_2b":
        from transformers.modeling_utils import PreTrainedModel
        if not hasattr(PreTrainedModel, "all_tied_weights_keys"):
            PreTrainedModel.all_tied_weights_keys = {}
        from transformers import AutoTokenizer, AutoModel
        import torchvision.transforms as T
        from torchvision.transforms import InterpolationMode
        model_dir = args.checkpoint
        tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True, fix_mistral_regex=True)
        model = AutoModel.from_pretrained(model_dir, trust_remote_code=True, dtype=torch.bfloat16,
                                          device_map=device).eval()
        transform = T.Compose([T.Lambda(lambda img: img.convert("RGB")),
                               T.Resize((448, 448), interpolation=InterpolationMode.BICUBIC),
                               T.ToTensor(),
                               T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))])

        def answer(processor, model, image):
            pixel = transform(image).unsqueeze(0).to(torch.bfloat16).to(model.device)
            cfg = {"max_new_tokens": 16, "do_sample": False}
            return model.chat(tokenizer, pixel, PROMPT, cfg)

        processor = tokenizer
    elif args.model == "qwen3vl2b":
        model_dir = args.checkpoint
        processor, model = load_qwen(model_dir, device)
        answer = answer_qwen
    else:
        model_dir = args.checkpoint
        processor, model = load_smol(model_dir, device)
        answer = answer_smol
    print("model loaded:", args.model, "| device", model.device, flush=True)

    items = build(args.images_root, args.per_class, args.seed)
    print("images:", len(items), "(", args.per_class, "per class max )", flush=True)
    confusion = {c: {d: 0 for d in CLASSES} for c in CLASSES}
    correct = 0
    unknown = 0
    t0 = time.time()
    for i, (path, truth) in enumerate(items):
        try:
            with Image.open(path) as im:
                pred = parse(answer(processor, model, im.convert("RGB")))
        except Exception as exc:  # noqa: BLE001
            print("  skip", os.path.basename(path), str(exc)[:80], flush=True)
            continue
        if pred is None:
            unknown += 1
            continue
        confusion[truth][pred] += 1
        correct += int(pred == truth)
        if (i + 1) % 50 == 0:
            print("  %d/%d acc %.3f (%.2f s/img)" % (i + 1, len(items), correct / (i + 1),
                                                     (time.time() - t0) / (i + 1)), flush=True)
    n = sum(sum(row.values()) for row in confusion.values())
    per_class = {}
    for c in CLASSES:
        total = sum(confusion[c].values())
        per_class[c] = round(confusion[c][c] / total, 4) if total else None
    acc = round(correct / n, 4) if n else 0.0
    macro = round(sum(v for v in per_class.values() if v is not None) / len([v for v in per_class.values() if v is not None]), 4)
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    payload = {"model": args.model, "images": n, "per_class_cap": args.per_class, "correct": correct,
               "accuracy": acc, "macro_accuracy": macro, "unknown_answers": unknown,
               "chance": round(1 / len(CLASSES), 4), "per_class": per_class,
               "confusion": confusion, "prompt": PROMPT,
               "wall_seconds": round(time.time() - t0, 1)}
    out = os.path.abspath(args.output)
    io.open(out, "x", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("accuracy %.4f | macro %.4f | unknown %d | chance %.3f" % (acc, macro, unknown, 1 / len(CLASSES)))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

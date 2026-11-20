# -*- coding: utf-8 -*-
"""Generate LLM captions with a locally loaded Qwen3-VL model (transformers, no LM Studio).

Same prompt, image pre-processing and JSONL schema as make_llm_caption_corpus.py (which used the LM Studio server), so
the resulting corpus can be used as an additional provenance arm in the LLM-caption scale comparison. The output is
resumable: lines already present in the output file are kept.

Usage
  python make_llm_caption_corpus_local.py --dataset rsicd --limit 3000 \
      --model-path local_runs/models/Qwen3-VL-2B-Instruct \
      --out corpora/rsicd/llmcaption2b.jsonl --batch-size 8
"""
import argparse
import io
import json
import os
import time

from PIL import Image
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT = ("Describe this remote sensing image in one sentence. Mention the main objects, their layout, and the "
          "land-cover type. Do not use a list; write one fluent sentence of 10 to 25 words.")


def load_image(path, max_side):
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, max_side / float(max(w, h)))
        if scale < 1.0:
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model-path", default="local_runs/models/Qwen3-VL-2B-Instruct")
    ap.add_argument("--out", default="")
    ap.add_argument("--max-side", type=int, default=768)
    ap.add_argument("--max-new-tokens", type=int, default=80)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--ids-file", default="", help="optional JSONL whose image_id order selects the images")
    args = ap.parse_args()

    from transformers import AutoProcessor, AutoModelForImageTextToText

    src = os.path.join(ROOT, "corpora", args.dataset, "human.jsonl")
    out = args.out or os.path.join(ROOT, "corpora", args.dataset, "llmcaption2b.jsonl")
    images_root = os.path.join(ROOT, "data", "rsicd" if args.dataset == "rsicd" else "nwpu_captions")
    model_path = os.path.join(ROOT, args.model_path) if not os.path.isabs(args.model_path) else args.model_path

    rows, seen = [], set()
    for line in io.open(src, encoding="utf-8"):
        r = json.loads(line)
        if r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        rows.append(r)
    if args.limit:
        rows = rows[:args.limit]
    if args.ids_file:
        by_id = {r["image_id"]: r for r in rows}
        ordered = [json.loads(line)["image_id"] for line in io.open(args.ids_file, encoding="utf-8")]
        rows = [by_id[i] for i in ordered if i in by_id]
        miss = [i for i in ordered if i not in by_id]
        if miss:
            print("  ids not found in %s: %d" % (src, len(miss)), flush=True)

    done = {}
    if os.path.exists(out):
        for line in io.open(out, encoding="utf-8"):
            r = json.loads(line)
            done[r["image_id"]] = r
    todo = [r for r in rows if r["image_id"] not in done]
    print("images %d | already captioned %d | todo %d | model %s | batch %d"
          % (len(rows), len(done), len(todo), model_path, args.batch_size), flush=True)

    dtype = getattr(torch, args.dtype)
    processor = AutoProcessor.from_pretrained(model_path)
    model = AutoModelForImageTextToText.from_pretrained(model_path, dtype=dtype, device_map=args.device)
    model.eval()
    print("model loaded | device %s | dtype %s" % (model.device, dtype), flush=True)

    def build(batch_rows):
        images, prompts = [], []
        for rr in batch_rows:
            image = load_image(os.path.join(images_root, rr["image_path"]), args.max_side)
            messages = [{"role": "user", "content": [{"type": "image"},
                                                    {"type": "text", "text": PROMPT}]}]
            prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
            images.append(image)
            prompts.append(prompt)
        inputs = processor(text=prompts, images=images, return_tensors="pt", padding=True).to(model.device)
        with torch.inference_mode():
            gen = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=True,
                                 temperature=0.2, top_p=0.9)
        trimmed = gen[:, inputs["input_ids"].shape[1]:]
        texts = processor.batch_decode(trimmed, skip_special_tokens=True)
        return [" ".join(tx.split()) for tx in texts]

    def single(row):
        image = load_image(os.path.join(images_root, row["image_path"]), args.max_side)
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = processor(text=[prompt], images=[image], return_tensors="pt").to(model.device)
        with torch.inference_mode():
            gen = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=True,
                                 temperature=0.2, top_p=0.9)
        trimmed = gen[0][inputs["input_ids"].shape[1]:]
        return " ".join(processor.decode(trimmed, skip_special_tokens=True).split())

    t0 = time.time()
    n_new = 0
    bs = max(1, args.batch_size)
    with io.open(out, "a", encoding="utf-8", newline="") as f:
        for start in range(0, len(todo), bs):
            batch_rows = todo[start:start + bs]
            texts = None
            if len(batch_rows) > 1:
                try:
                    texts = build(batch_rows)
                except Exception as exc:  # noqa: BLE001
                    print("  batch failed (%s), falling back to single" % str(exc)[:100], flush=True)
                    texts = None
            if texts is None:
                texts = []
                for rr in batch_rows:
                    text = None
                    for attempt in range(3):
                        try:
                            text = single(rr)
                            break
                        except Exception as exc:  # noqa: BLE001
                            if attempt == 2:
                                print("  skip %s: %s" % (rr["image_id"], str(exc)[:100]), flush=True)
                            else:
                                time.sleep(1 + attempt)
                    texts.append(text or "")
            for rr, text in zip(batch_rows, texts):
                if not text:
                    continue
                rec = {"image_id": rr["image_id"], "image_path": rr["image_path"], "split": rr["split"],
                       "text": text, "metadata": rr.get("metadata", {}), "derived_objects": {},
                       "boxes": [], "source": "llm", "generator": "Qwen3-VL-2B-Instruct"}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_new += 1
            f.flush()
            if n_new and n_new % 50 < bs:
                dt = time.time() - t0
                print("  %d/%d captioned (%.2f s/img, %.1f min elapsed)"
                      % (n_new, len(todo), dt / n_new, dt / 60), flush=True)
    print("wrote %s | new %d" % (out, n_new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
